from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Product, Review
from backend.app.schemas import ReviewAggregate, ReviewCreate, ReviewRead

router = APIRouter(prefix="/api/products/{product_id}/reviews", tags=["reviews"])


def _aggregate(db: Session, product: Product) -> ReviewAggregate:
    reviews = (
        db.query(Review)
        .filter(Review.product_id == product.id)
        .order_by(Review.created_at.desc(), Review.id.desc())
        .all()
    )
    count = len(reviews)
    average = round(sum(review.rating for review in reviews) / count, 2) if count else float(product.rating)
    return ReviewAggregate(average_rating=average, count=count, reviews=reviews)


def _recalculate_product_rating(db: Session, product: Product) -> None:
    aggregate = _aggregate(db, product)
    product.rating = Decimal(str(aggregate.average_rating))
    db.add(product)


@router.get("", response_model=ReviewAggregate)
def list_reviews(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Dieses Produkt ist leider nicht mehr verfuegbar.")
    return _aggregate(db, product)


@router.post("", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
def create_review(product_id: int, payload: ReviewCreate, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Dieses Produkt ist leider nicht mehr verfuegbar.")
    review = Review(
        product_id=product.id,
        author=(payload.author or "Gast").strip() or "Gast",
        rating=payload.rating,
        comment=payload.comment.strip(),
    )
    db.add(review)
    db.flush()
    _recalculate_product_rating(db, product)
    db.commit()
    db.refresh(review)
    return review
