from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Product
from backend.app.schemas import ProductDetail, ProductListItem

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=list[ProductListItem])
def list_products(
    brand: str | None = None,
    search: str | None = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
):
    query = db.query(Product)
    if brand:
        query = query.filter(Product.brand.ilike(f"%{brand}%"))
    if search:
        term = f"%{search}%"
        query = query.filter(or_(Product.name.ilike(term), Product.short_description.ilike(term)))
    return query.order_by(Product.is_new.desc(), Product.id.asc()).all()


@router.get("/{product_id}", response_model=ProductDetail)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Dieses Produkt ist leider nicht mehr verfuegbar.")
    return product
