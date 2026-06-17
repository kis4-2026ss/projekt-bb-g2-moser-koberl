from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ProductListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    brand: str
    price: Decimal
    currency: str
    image_url: str
    short_description: str
    is_new: bool
    rating: float


class ProductDetail(ProductListItem):
    long_description: str
    sizes: list[int]
    color: str
    material: str
    stock: int


class ReviewCreate(BaseModel):
    author: str | None = Field(default=None, max_length=100)
    rating: int = Field(ge=1, le=5)
    comment: str = Field(min_length=3, max_length=1000)


class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    author: str | None
    rating: int
    comment: str
    created_at: datetime


class ReviewAggregate(BaseModel):
    average_rating: float
    count: int
    reviews: list[ReviewRead]


class CartItemCreate(BaseModel):
    product_id: int
    size: int
    quantity: int = Field(ge=1)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1)


class CartItemRead(BaseModel):
    id: int
    product_id: int
    name: str
    brand: str
    price: Decimal
    currency: str
    image_url: str
    size: int
    quantity: int
    line_total: Decimal


class CartRead(BaseModel):
    items: list[CartItemRead]
    item_count: int
    subtotal: Decimal
    total: Decimal


class ShippingCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    street: str = Field(min_length=3, max_length=160)
    zip: str = Field(min_length=3, max_length=20)
    city: str = Field(min_length=2, max_length=100)
    country: str = Field(min_length=2, max_length=80)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=160)


class OrderCreate(BaseModel):
    shipping: ShippingCreate
    payment_method: Literal["invoice", "credit_card_demo"]


class ShippingRead(ShippingCreate):
    pass


class OrderItemRead(BaseModel):
    id: int
    product_id: int
    name: str
    brand: str
    price: Decimal
    image_url: str
    size: int
    quantity: int
    line_total: Decimal


class OrderRead(BaseModel):
    order_id: int
    status: str
    created_at: datetime
    shipping: ShippingRead
    payment_method: str
    items: list[OrderItemRead]
    subtotal: Decimal
    total: Decimal
