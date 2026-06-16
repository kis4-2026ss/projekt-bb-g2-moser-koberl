"""Order API endpoints."""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from backend.app.api.cart import clear_cart, get_stored_cart_items
from backend.app.database import get_db
from backend.app.models import Order, OrderItem, Sneaker
from backend.app.schemas import OrderCreate, OrderCreated, OrderRead

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=OrderCreated, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
) -> OrderCreated:
    """Create an order from the current cart and clear the cart."""
    cart_items = get_stored_cart_items()
    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty",
        )

    order_lines: list[OrderItem] = []
    subtotal = Decimal("0.00")

    for cart_item in cart_items:
        product = db.get(Sneaker, cart_item.product_id)
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart contains an unavailable product",
            )

        if cart_item.size not in product.sizes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart contains an unavailable product size",
            )

        if cart_item.quantity > product.stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart quantity exceeds available stock",
            )

        line_total = product.price * cart_item.quantity
        subtotal += line_total
        order_lines.append(
            OrderItem(
                product_id=product.id,
                name_snapshot=product.name,
                brand_snapshot=product.brand,
                price_snapshot=product.price,
                image_url_snapshot=product.image_url,
                size=cart_item.size,
                quantity=cart_item.quantity,
                line_total=line_total,
            )
        )
        product.stock -= cart_item.quantity

    order = Order(
        status="created",
        shipping_name=payload.shipping.name,
        shipping_street=payload.shipping.street,
        shipping_zip=payload.shipping.zip,
        shipping_city=payload.shipping.city,
        shipping_country=payload.shipping.country,
        email=str(payload.shipping.email),
        payment_method=payload.payment_method,
        subtotal=subtotal,
        total=subtotal,
        items=order_lines,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    clear_cart()

    return OrderCreated(order_id=order.id, status=order.status, total=order.total)


@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: int, db: Session = Depends(get_db)) -> Order:
    """Return a persisted order or 404 when it does not exist."""
    order = db.get(
        Order,
        order_id,
        options=[selectinload(Order.items)],
    )
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

