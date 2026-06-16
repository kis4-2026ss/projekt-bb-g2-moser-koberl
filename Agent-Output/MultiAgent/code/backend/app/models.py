"""SQLAlchemy ORM models for the e-commerce application."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from backend.app.database import Base


class Sneaker(Base):
    """Product table containing sneaker catalog data."""

    __tablename__ = "sneakers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    brand = Column(String, nullable=False, index=True)
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, nullable=False, default="EUR")
    short_description = Column(String, nullable=False)
    long_description = Column(String, nullable=False)
    image_url = Column(String, nullable=False)
    sizes = Column(JSON, nullable=False)
    color = Column(String, nullable=False)
    material = Column(String, nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    rating = Column(Float, nullable=False, default=0.0)
    is_new = Column(Boolean, nullable=False, default=False)

    reviews = relationship(
        "Review",
        back_populates="product",
        cascade="all, delete-orphan",
    )
    order_items = relationship("OrderItem", back_populates="product")

    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_sneaker_price_non_negative"),
        CheckConstraint("stock >= 0", name="ck_sneaker_stock_non_negative"),
        CheckConstraint(
            "rating >= 0 AND rating <= 5",
            name="ck_sneaker_rating_range",
        ),
    )


class Review(Base):
    """Customer review for a sneaker product."""

    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(
        Integer,
        ForeignKey("sneakers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author = Column(String, nullable=True)
    rating = Column(Integer, nullable=False)
    comment = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    product = relationship("Sneaker", back_populates="reviews")

    __table_args__ = (
        CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="ck_review_rating_range",
        ),
    )


class Order(Base):
    """Order header with shipping, payment, and totals."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    status = Column(String, nullable=False, default="created")
    shipping_name = Column(String, nullable=False)
    shipping_street = Column(String, nullable=False)
    shipping_zip = Column(String, nullable=False)
    shipping_city = Column(String, nullable=False)
    shipping_country = Column(String, nullable=False)
    email = Column(String, nullable=False)
    payment_method = Column(String, nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)

    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="ck_order_subtotal_non_negative"),
        CheckConstraint("total >= 0", name="ck_order_total_non_negative"),
    )


class OrderItem(Base):
    """Immutable snapshot of a product line inside an order."""

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = Column(
        Integer,
        ForeignKey("sneakers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name_snapshot = Column(String, nullable=False)
    brand_snapshot = Column(String, nullable=False)
    price_snapshot = Column(Numeric(10, 2), nullable=False)
    image_url_snapshot = Column(String, nullable=False)
    size = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    line_total = Column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Sneaker", back_populates="order_items")

    __table_args__ = (
        CheckConstraint(
            "price_snapshot >= 0",
            name="ck_order_item_price_non_negative",
        ),
        CheckConstraint(
            "quantity > 0",
            name="ck_order_item_quantity_positive",
        ),
        CheckConstraint(
            "line_total >= 0",
            name="ck_order_item_line_total_non_negative",
        ),
    )
