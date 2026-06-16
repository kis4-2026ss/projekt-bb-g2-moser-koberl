"""Pydantic schemas for API request and response payloads."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class SneakerRead(BaseModel):
    """Public representation of a sneaker product."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    brand: str
    price: Decimal
    currency: str
    short_description: str
    long_description: str
    image_url: str
    sizes: list[str]
    color: str
    material: str
    stock: int
    rating: float
    is_new: bool

    @field_serializer("price")
    def serialize_price(self, value: Decimal) -> float:
        """Return money values as JSON numbers for frontend consumption."""
        return float(value)


class CartItemCreate(BaseModel):
    """Payload for adding a product to the cart."""

    product_id: int = Field(gt=0)
    size: str = Field(min_length=1, max_length=20)
    quantity: int = Field(gt=0)


class CartItemUpdate(BaseModel):
    """Payload for updating a cart item quantity."""

    quantity: int = Field(gt=0)


class CartItemRead(BaseModel):
    """Cart line enriched with product data."""

    item_id: int
    product_id: int
    name: str
    brand: str
    price: Decimal
    currency: str
    image_url: str
    size: str
    quantity: int
    line_total: Decimal

    @field_serializer("price", "line_total")
    def serialize_money(self, value: Decimal) -> float:
        """Return money values as JSON numbers for frontend consumption."""
        return float(value)


class CartRead(BaseModel):
    """Current shopping cart response."""

    items: list[CartItemRead]
    subtotal: Decimal
    total: Decimal
    currency: str = "EUR"

    @field_serializer("subtotal", "total")
    def serialize_totals(self, value: Decimal) -> float:
        """Return money values as JSON numbers for frontend consumption."""
        return float(value)


class ShippingAddress(BaseModel):
    """Shipping and customer contact data for checkout."""

    name: str = Field(min_length=1, max_length=255)
    street: str = Field(min_length=1, max_length=255)
    zip: str = Field(min_length=1, max_length=30)
    city: str = Field(min_length=1, max_length=120)
    country: str = Field(min_length=1, max_length=120)
    email: str = Field(
        min_length=3,
        max_length=255,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )


class OrderCreate(BaseModel):
    """Payload for creating an order from the current cart."""

    shipping: ShippingAddress
    payment_method: str = Field(min_length=1, max_length=80)


class OrderItemRead(BaseModel):
    """Public representation of a persisted order line."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    name_snapshot: str
    brand_snapshot: str
    price_snapshot: Decimal
    image_url_snapshot: str
    size: str
    quantity: int
    line_total: Decimal

    @field_serializer("price_snapshot", "line_total")
    def serialize_money(self, value: Decimal) -> float:
        """Return money values as JSON numbers for frontend consumption."""
        return float(value)


class OrderRead(BaseModel):
    """Public representation of an order."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    status: str
    shipping_name: str
    shipping_street: str
    shipping_zip: str
    shipping_city: str
    shipping_country: str
    email: str
    payment_method: str
    subtotal: Decimal
    total: Decimal
    items: list[OrderItemRead]

    @field_serializer("subtotal", "total")
    def serialize_totals(self, value: Decimal) -> float:
        """Return money values as JSON numbers for frontend consumption."""
        return float(value)


class OrderCreated(BaseModel):
    """Response returned after successful checkout."""

    order_id: int
    status: str
    total: Decimal

    @field_serializer("total")
    def serialize_total(self, value: Decimal) -> float:
        """Return money values as JSON numbers for frontend consumption."""
        return float(value)


class ReviewCreate(BaseModel):
    """Payload for creating a product review."""

    author: str | None = Field(default=None, max_length=120)
    rating: int = Field(ge=1, le=5)
    comment: str = Field(min_length=1, max_length=1000)


class ReviewRead(BaseModel):
    """Public representation of a customer review."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    author: str | None
    rating: int
    comment: str
    created_at: datetime


class ProductReviewsRead(BaseModel):
    """Review listing with aggregate product rating."""

    average_rating: float
    reviews: list[ReviewRead]
