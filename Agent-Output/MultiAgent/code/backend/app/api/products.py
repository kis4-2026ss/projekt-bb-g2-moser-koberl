"""Product API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Sneaker
from backend.app.schemas import SneakerRead

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=list[SneakerRead])
def list_products(db: Session = Depends(get_db)) -> list[Sneaker]:
    """Return all products in catalog order."""
    return list(db.scalars(select(Sneaker).order_by(Sneaker.id)).all())


@router.get("/{product_id}", response_model=SneakerRead)
def get_product(product_id: int, db: Session = Depends(get_db)) -> Sneaker:
    """Return one product or 404 when it does not exist."""
    product = db.get(Sneaker, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

