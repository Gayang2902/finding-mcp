from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db, Product, Coupon
from ..auth import get_current_user, require_admin

router = APIRouter(tags=["products"])


# ── Public product endpoints ──────────────────────────────────────────────────

@router.get("/products")
def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.is_active == True).all()
    return [
        {"id": p.id, "name": p.name, "price": p.price,
         "stock": p.stock, "discount_pct": p.discount_pct}
        for p in products
    ]


@router.get("/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(404, "Product not found")
    return {"id": p.id, "name": p.name, "price": p.price,
            "stock": p.stock, "category": p.category}


# ── Admin endpoints ───────────────────────────────────────────────────────────

class ProductIn(BaseModel):
    name: str
    price: float
    stock: int
    category: str = "general"
    discount_pct: float = 0.0


class CouponIn(BaseModel):
    code: str
    discount_pct: float
    max_uses: int = 100
    min_order_amount: float = 0.0


@router.post("/admin/products")
def create_product(
    req: ProductIn,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    product = Product(**req.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return {"id": product.id, "name": product.name}


@router.post("/admin/coupons")
def create_coupon(
    req: CouponIn,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    coupon = Coupon(**req.model_dump())
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return {"id": coupon.id, "code": coupon.code}


@router.get("/admin/users")
def list_users(
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    from ..database import User
    users = db.query(User).all()
    return [{"id": u.id, "username": u.username,
             "balance": u.balance, "role": u.role} for u in users]
