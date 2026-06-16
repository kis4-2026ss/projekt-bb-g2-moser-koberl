"""Review API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Review, Sneaker
from backend.app.schemas import ProductReviewsRead, ReviewCreate, ReviewRead

router = APIRouter(prefix="/api/products", tags=["reviews"])


def _get_product(db: Session, product_id: int) -> Sneaker:
    """Return a product or raise a 404 HTTP error."""
    product = db.get(Sneaker, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def _refresh_product_rating(db: Session, product: Sneaker) -> None:
    """Persist the rounded average rating on the product record."""
    average = db.scalar(
        select(func.avg(Review.rating)).where(Review.product_id == product.id)
    )
    product.rating = round(float(average or 0), 1)


@router.get("/{product_id}/reviews", response_model=ProductReviewsRead)
def list_reviews(
    product_id: int,
    db: Session = Depends(get_db),
) -> ProductReviewsRead:
    """Return review aggregate and reviews for one product."""
    _get_product(db, product_id)
    reviews = list(
        db.scalars(
            select(Review)
            .where(Review.product_id == product_id)
            .order_by(Review.created_at.desc(), Review.id.desc())
        ).all()
    )
    average = (
        sum(review.rating for review in reviews) / len(reviews)
        if reviews
        else 0.0
    )
    return ProductReviewsRead(
        average_rating=round(average, 1),
        reviews=reviews,
    )


@router.post(
    "/{product_id}/reviews",
    response_model=ReviewRead,
    status_code=status.HTTP_201_CREATED,
)
def create_review(
    product_id: int,
    payload: ReviewCreate,
    db: Session = Depends(get_db),
) -> Review:
    """Create a review for a product and update its aggregate rating."""
    product = _get_product(db, product_id)
    review = Review(
        product_id=product.id,
        author=payload.author,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(review)
    db.flush()
    _refresh_product_rating(db, product)
    db.commit()
    db.refresh(review)
    return review
