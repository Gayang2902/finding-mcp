from .database import SessionLocal, User, Product, Coupon
from .auth import hash_password


def run():
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return

        users = [
            User(username="alice", email="alice@example.com",
                 hashed_pw=hash_password("password123"),
                 balance=500.0, role="user", is_verified=True,
                 referral_code="ALICE10"),
            User(username="bob", email="bob@example.com",
                 hashed_pw=hash_password("password123"),
                 balance=100.0, role="user", is_verified=False,
                 referral_code="BOB10"),
            User(username="admin", email="admin@example.com",
                 hashed_pw=hash_password("admin1234"),
                 balance=0.0, role="admin", is_verified=True,
                 referral_code="ADMIN00"),
        ]
        db.add_all(users)

        products = [
            Product(name="Laptop",     price=999.0,  stock=5,   category="electronics"),
            Product(name="Headphones", price=149.0,  stock=20,  category="electronics"),
            Product(name="T-Shirt",    price=29.0,   stock=100, category="clothing"),
            Product(name="Book",       price=15.0,   stock=50,  category="books",
                    discount_pct=10.0),
        ]
        db.add_all(products)

        coupons = [
            Coupon(code="SAVE10",   discount_pct=10.0, max_uses=100, min_order_amount=50.0),
            Coupon(code="VIP50",    discount_pct=50.0, max_uses=10),
            Coupon(code="NEWUSER",  discount_pct=20.0, max_uses=1000),
            Coupon(code="FLASH100", discount_pct=100.0, max_uses=5),
        ]
        db.add_all(coupons)
        db.commit()
    finally:
        db.close()
