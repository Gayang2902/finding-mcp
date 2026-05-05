"""
app/routers/orders.py

BUG-1: 음수 수량 허용
BUG-2: 쿠폰 중첩
BUG-3: TOCTOU double-spend
BUG-5: 중복 취소 환불
BUG-6: 클라이언트 가격 신뢰
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db, User, Product, Order, OrderItem, Coupon
from ..auth import get_current_user

router = APIRouter(prefix="/orders", tags=["orders"])


class OrderItemIn(BaseModel):
    product_id: int
    quantity: int


class PlaceOrderRequest(BaseModel):
    items: list[OrderItemIn]
    coupon_codes: list[str] = []


class QuickOrderRequest(BaseModel):
    """BUG-6: 클라이언트가 total을 직접 전달."""
    items: list[OrderItemIn]
    total: float                  # ← 서버에서 재계산 안 함


def _apply_coupons(total: float, codes: list[str], db: Session) -> float:
    """BUG-2: 쿠폰 개수 제한 없이 전부 적용."""
    for code in codes:
        coupon = db.query(Coupon).filter(Coupon.code == code).first()
        if (coupon and coupon.is_active
                and coupon.used_count < coupon.max_uses
                and total >= coupon.min_order_amount):
            total *= (1 - coupon.discount_pct / 100)
    return total


@router.post("/")
def place_order(
    req: PlaceOrderRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    total = 0.0
    line_items = []

    for item in req.items:
        # BUG-1: quantity 음수 허용
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product or not product.is_active:
            raise HTTPException(404, f"Product {item.product_id} not found")
        if product.stock < item.quantity:
            raise HTTPException(400, "Insufficient stock")

        unit_price = product.price * (1 - product.discount_pct / 100)
        total += unit_price * item.quantity
        line_items.append((product, item.quantity, unit_price))

    total = _apply_coupons(total, req.coupon_codes, db)

    # BUG-3: 잔액 읽기와 차감 사이 원자성 없음
    if user.balance < total:
        raise HTTPException(400, f"Insufficient balance: need {total:.2f}")

    user.balance -= total   # non-atomic

    order = Order(
        user_id=user.id,
        total=total,
        status="paid",
        coupon_code=req.coupon_codes[0] if req.coupon_codes else None,
    )
    db.add(order)
    db.flush()

    for product, qty, unit_price in line_items:
        db.add(OrderItem(
            order_id=order.id, product_id=product.id,
            quantity=qty, unit_price=unit_price,
        ))
        product.stock -= qty

    for code in req.coupon_codes:
        coupon = db.query(Coupon).filter(Coupon.code == code).first()
        if coupon:
            coupon.used_count += 1  # BUG-3: 레이스 윈도우 이후 증가

    db.commit()
    db.refresh(order)
    return {"order_id": order.id, "total": order.total, "status": order.status}


@router.post("/quick")
def quick_order(
    req: QuickOrderRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """BUG-6: total을 클라이언트 값 그대로 사용."""
    if user.balance < req.total:
        raise HTTPException(400, "Insufficient balance")

    user.balance -= req.total

    order = Order(user_id=user.id, total=req.total, status="paid")
    db.add(order)
    db.flush()

    for item in req.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            db.add(OrderItem(
                order_id=order.id, product_id=product.id,
                quantity=item.quantity, unit_price=req.total,
            ))

    db.commit()
    db.refresh(order)
    return {"order_id": order.id, "total": order.total}


@router.post("/{order_id}/cancel")
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """BUG-5: 상태 검사 없이 반복 취소 가능 → 중복 환불."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")
    if order.user_id != user.id:
        raise HTTPException(403, "Not your order")

    # 상태 guard 없음 — cancelled 상태에서도 재실행됨
    user.balance += order.total
    order.status  = "cancelled"
    db.commit()

    return {"order_id": order.id, "refunded": order.total, "balance": user.balance}


@router.get("/")
def list_orders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    orders = db.query(Order).filter(Order.user_id == user.id).all()
    return [{"id": o.id, "total": o.total, "status": o.status} for o in orders]
