from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    Boolean, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

DATABASE_URL = "sqlite:///./shop.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True, index=True)
    username      = Column(String, unique=True, nullable=False)
    email         = Column(String, unique=True, nullable=False)
    hashed_pw     = Column(String, nullable=False)
    role          = Column(String, default="user")   # user | admin
    balance       = Column(Float,  default=0.0)
    is_verified   = Column(Boolean, default=False)
    referral_code = Column(String, unique=True, nullable=True)
    referral_count= Column(Integer, default=0)
    created_at    = Column(DateTime, default=datetime.utcnow)

    orders   = relationship("Order",   back_populates="user")


class Product(Base):
    __tablename__ = "products"
    id           = Column(Integer, primary_key=True, index=True)
    name         = Column(String, nullable=False)
    price        = Column(Float,  nullable=False)
    stock        = Column(Integer, default=0)
    category     = Column(String, default="general")
    discount_pct = Column(Float, default=0.0)
    is_active    = Column(Boolean, default=True)


class Coupon(Base):
    __tablename__ = "coupons"
    id               = Column(Integer, primary_key=True, index=True)
    code             = Column(String, unique=True, nullable=False)
    discount_pct     = Column(Float, nullable=False)
    max_uses         = Column(Integer, default=100)
    used_count       = Column(Integer, default=0)
    min_order_amount = Column(Float, default=0.0)
    is_active        = Column(Boolean, default=True)


class Order(Base):
    __tablename__ = "orders"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    total       = Column(Float, nullable=False)
    status      = Column(String, default="pending")  # pending|paid|shipped|cancelled
    coupon_code = Column(String, nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)

    user  = relationship("User",      back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete")


class OrderItem(Base):
    __tablename__ = "order_items"
    id         = Column(Integer, primary_key=True, index=True)
    order_id   = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity   = Column(Integer, nullable=False)
    unit_price = Column(Float,   nullable=False)

    order   = relationship("Order",   back_populates="items")
    product = relationship("Product")
