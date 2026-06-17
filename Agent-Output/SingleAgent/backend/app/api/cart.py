from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from backend.app.api.deps import cart_response, require_cart_item
from backend.app.database import get_db
from backend.app.models import CartItem, Product
from backend.app.schemas import CartItemCreate, CartItemUpdate, CartRead
from backend.app.session import get_session_token

router = APIRouter(prefix="/api/cart", tags=["cart"])


@router.get("", response_model=CartRead)
def get_cart(request: Request, response: Response, db: Session = Depends(get_db)):
    session_token = get_session_token(request, response)
    return cart_response(db, session_token)


@router.post("/items", response_model=CartRead, status_code=status.HTTP_201_CREATED)
def add_cart_item(payload: CartItemCreate, request: Request, response: Response, db: Session = Depends(get_db)):
    session_token = get_session_token(request, response)
    product = db.get(Product, payload.product_id)
    if not product or product.stock <= 0:
        raise HTTPException(status_code=404, detail="Dieses Produkt ist leider nicht mehr verfuegbar.")
    if payload.size not in product.sizes:
        raise HTTPException(status_code=400, detail="Diese Groesse ist aktuell nicht verfuegbar.")
    if payload.quantity > product.stock:
        raise HTTPException(status_code=400, detail="Die gewuenschte Menge ist aktuell nicht verfuegbar.")

    item = (
        db.query(CartItem)
        .filter(
            CartItem.session_token == session_token,
            CartItem.product_id == product.id,
            CartItem.size == payload.size,
        )
        .first()
    )
    if item:
        item.quantity += payload.quantity
    else:
        item = CartItem(
            session_token=session_token,
            product_id=product.id,
            size=payload.size,
            quantity=payload.quantity,
        )
        db.add(item)
    db.commit()
    return cart_response(db, session_token)


@router.patch("/items/{item_id}", response_model=CartRead)
def update_cart_item(
    item_id: int,
    payload: CartItemUpdate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    session_token = get_session_token(request, response)
    item = require_cart_item(db, item_id, session_token)
    if payload.quantity > item.product.stock:
        raise HTTPException(status_code=400, detail="Die gewuenschte Menge ist aktuell nicht verfuegbar.")
    item.quantity = payload.quantity
    db.commit()
    return cart_response(db, session_token)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cart_item(item_id: int, request: Request, response: Response, db: Session = Depends(get_db)):
    session_token = get_session_token(request, response)
    item = require_cart_item(db, item_id, session_token)
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
