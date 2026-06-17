from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.models import CartItem, Order, OrderItem
from backend.app.schemas import CartItemRead, CartRead, OrderItemRead, OrderRead, ShippingRead


def money(value: Decimal | float | int) -> Decimal:
    return Decimal(value).quantize(Decimal("0.01"))


def cart_response(db: Session, session_token: str) -> CartRead:
    items = (
        db.query(CartItem)
        .filter(CartItem.session_token == session_token)
        .order_by(CartItem.id.asc())
        .all()
    )
    rows: list[CartItemRead] = []
    for item in items:
        line_total = money(item.product.price * item.quantity)
        rows.append(
            CartItemRead(
                id=item.id,
                product_id=item.product_id,
                name=item.product.name,
                brand=item.product.brand,
                price=item.product.price,
                currency=item.product.currency,
                image_url=item.product.image_url,
                size=item.size,
                quantity=item.quantity,
                line_total=line_total,
            )
        )
    subtotal = money(sum((row.line_total for row in rows), Decimal("0.00")))
    return CartRead(items=rows, item_count=sum(row.quantity for row in rows), subtotal=subtotal, total=subtotal)


def order_response(order: Order) -> OrderRead:
    return OrderRead(
        order_id=order.id,
        status=order.status,
        created_at=order.created_at,
        shipping=ShippingRead(
            name=order.shipping_name,
            street=order.shipping_street,
            zip=order.shipping_zip,
            city=order.shipping_city,
            country=order.shipping_country,
            email=order.shipping_email,
        ),
        payment_method=order.payment_method,
        items=[
            OrderItemRead(
                id=item.id,
                product_id=item.product_id,
                name=item.name_snapshot,
                brand=item.brand_snapshot,
                price=item.price_snapshot,
                image_url=item.image_url_snapshot,
                size=item.size,
                quantity=item.quantity,
                line_total=item.line_total,
            )
            for item in order.items
        ],
        subtotal=order.subtotal,
        total=order.total,
    )


def require_cart_item(db: Session, item_id: int, session_token: str) -> CartItem:
    item = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.session_token == session_token)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Diese Warenkorb-Position wurde nicht gefunden.")
    return item
