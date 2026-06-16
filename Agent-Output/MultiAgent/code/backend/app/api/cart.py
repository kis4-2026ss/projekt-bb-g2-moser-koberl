"""Shopping cart API endpoints.

The architecture defines no cart table, so the cart is kept in process memory.
This is suitable for the single-user demo frontend and keeps persistence scoped
to the declared order schema.
"""

from dataclasses import dataclass
from decimal import Decimal
from itertools import count
from threading import Lock

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Sneaker
from backend.app.schemas import (
    CartItemCreate,
    CartItemRead,
    CartItemUpdate,
    CartRead,
)

router = APIRouter(prefix="/api/cart", tags=["cart"])


@dataclass
class StoredCartItem:
    """Minimal cart state stored between requests."""

    item_id: int
    product_id: int
    size: str
    quantity: int


_cart_items: dict[int, StoredCartItem] = {}
_cart_item_ids = count(1)
_cart_lock = Lock()


def _get_product(db: Session, product_id: int) -> Sneaker:
    """Return a product or raise a 404 HTTP error."""
    product = db.get(Sneaker, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def _validate_cart_item(product: Sneaker, size: str, quantity: int) -> None:
    """Validate size and stock constraints for a cart line."""
    if size not in product.sizes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected size is not available for this product",
        )

    if quantity > product.stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requested quantity exceeds available stock",
        )


def get_stored_cart_items() -> list[StoredCartItem]:
    """Return a stable snapshot of the current cart state."""
    with _cart_lock:
        return list(_cart_items.values())


def clear_cart() -> None:
    """Remove all cart items after successful checkout."""
    with _cart_lock:
        _cart_items.clear()


def build_cart_response(db: Session) -> CartRead:
    """Build a cart response from stored cart lines and current products."""
    response_items: list[CartItemRead] = []
    subtotal = Decimal("0.00")

    for stored_item in get_stored_cart_items():
        product = db.get(Sneaker, stored_item.product_id)
        if product is None:
            continue

        line_total = product.price * stored_item.quantity
        subtotal += line_total
        response_items.append(
            CartItemRead(
                item_id=stored_item.item_id,
                product_id=product.id,
                name=product.name,
                brand=product.brand,
                price=product.price,
                currency=product.currency,
                image_url=product.image_url,
                size=stored_item.size,
                quantity=stored_item.quantity,
                line_total=line_total,
            )
        )

    return CartRead(items=response_items, subtotal=subtotal, total=subtotal)


@router.get("", response_model=CartRead)
def get_cart(db: Session = Depends(get_db)) -> CartRead:
    """Return the current shopping cart."""
    return build_cart_response(db)


@router.post(
    "/items",
    response_model=CartItemRead,
    status_code=status.HTTP_201_CREATED,
)
def add_cart_item(
    payload: CartItemCreate,
    db: Session = Depends(get_db),
) -> CartItemRead:
    """Add a product line to the cart or increase an existing line."""
    product = _get_product(db, payload.product_id)

    with _cart_lock:
        existing = next(
            (
                item
                for item in _cart_items.values()
                if item.product_id == payload.product_id
                and item.size == payload.size
            ),
            None,
        )
        requested_quantity = payload.quantity
        if existing is not None:
            requested_quantity += existing.quantity

        _validate_cart_item(product, payload.size, requested_quantity)

        if existing is None:
            item_id = next(_cart_item_ids)
            _cart_items[item_id] = StoredCartItem(
                item_id=item_id,
                product_id=payload.product_id,
                size=payload.size,
                quantity=payload.quantity,
            )
        else:
            existing.quantity = requested_quantity
            item_id = existing.item_id

    cart = build_cart_response(db)
    return next(item for item in cart.items if item.item_id == item_id)


@router.patch(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def update_cart_item(
    item_id: int,
    payload: CartItemUpdate,
    db: Session = Depends(get_db),
) -> Response:
    """Update the quantity of an existing cart item."""
    with _cart_lock:
        stored_item = _cart_items.get(item_id)
        if stored_item is None:
            raise HTTPException(status_code=404, detail="Cart item not found")

        product = _get_product(db, stored_item.product_id)
        _validate_cart_item(product, stored_item.size, payload.quantity)
        stored_item.quantity = payload.quantity

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_cart_item(item_id: int) -> Response:
    """Remove an item from the current cart."""
    with _cart_lock:
        if item_id not in _cart_items:
            raise HTTPException(status_code=404, detail="Cart item not found")
        del _cart_items[item_id]

    return Response(status_code=status.HTTP_204_NO_CONTENT)
