from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, Boolean, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    brand: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    short_description: Mapped[str] = mapped_column(String(255), nullable=False)
    long_description: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str] = mapped_column(String(800), nullable=False)
    sizes: Mapped[list[int]] = mapped_column(JSON, nullable=False)
    color: Mapped[str] = mapped_column(String(80), nullable=False)
    material: Mapped[str] = mapped_column(String(120), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False)
    rating: Mapped[float] = mapped_column(Numeric(3, 2), default=0, nullable=False)
    is_new: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    reviews: Mapped[list["Review"]] = relationship(back_populates="product", cascade="all, delete-orphan")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    author: Mapped[str] = mapped_column(String(100), nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    product: Mapped[Product] = relationship(back_populates="reviews")


class CartItem(Base):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_token: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    product: Mapped[Product] = relationship()


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="confirmed", nullable=False)
    shipping_name: Mapped[str] = mapped_column(String(120), nullable=False)
    shipping_street: Mapped[str] = mapped_column(String(160), nullable=False)
    shipping_zip: Mapped[str] = mapped_column(String(20), nullable=False)
    shipping_city: Mapped[str] = mapped_column(String(100), nullable=False)
    shipping_country: Mapped[str] = mapped_column(String(80), nullable=False)
    shipping_email: Mapped[str] = mapped_column(String(160), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(40), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    session_token: Mapped[str] = mapped_column(String(80), index=True, nullable=False)

    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name_snapshot: Mapped[str] = mapped_column(String(120), nullable=False)
    brand_snapshot: Mapped[str] = mapped_column(String(80), nullable=False)
    price_snapshot: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    image_url_snapshot: Mapped[str] = mapped_column(String(800), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    order: Mapped[Order] = relationship(back_populates="items")
