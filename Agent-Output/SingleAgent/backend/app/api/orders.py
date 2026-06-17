from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session, selectinload

from backend.app.api.deps import cart_response, money, order_response
from backend.app.database import get_db
from backend.app.models import CartItem, Order, OrderItem
from backend.app.schemas import OrderCreate, OrderRead
from backend.app.session import get_session_token

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, request: Request, response: Response, db: Session = Depends(get_db)):
    session_token = get_session_token(request, response)
    cart = cart_response(db, session_token)
    if not cart.items:
        raise HTTPException(status_code=400, detail="Dein Warenkorb ist leer.")

    order = Order(
        status="confirmed",
        shipping_name=payload.shipping.name,
        shipping_street=payload.shipping.street,
        shipping_zip=payload.shipping.zip,
        shipping_city=payload.shipping.city,
        shipping_country=payload.shipping.country,
        shipping_email=str(payload.shipping.email),
        payment_method=payload.payment_method,
        subtotal=cart.subtotal,
        total=cart.total,
        session_token=session_token,
    )
    db.add(order)
    db.flush()

    cart_items = (
        db.query(CartItem)
        .filter(CartItem.session_token == session_token)
        .order_by(CartItem.id.asc())
        .all()
    )
    for item in cart_items:
        line_total = money(item.product.price * item.quantity)
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                name_snapshot=item.product.name,
                brand_snapshot=item.product.brand,
                price_snapshot=item.product.price,
                image_url_snapshot=item.product.image_url,
                size=item.size,
                quantity=item.quantity,
                line_total=line_total,
            )
        )
        db.delete(item)
    db.commit()
    order = (
        db.query(Order)
        .options(selectinload(Order.items))
        .filter(Order.id == order.id)
        .one()
    )
    return order_response(order)


@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).options(selectinload(Order.items)).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Diese Bestellung wurde nicht gefunden.")
    return order_response(order)
