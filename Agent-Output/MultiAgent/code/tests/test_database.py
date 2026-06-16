from decimal import Decimal

import pytest
from sqlalchemy import exc, select
from sqlalchemy.orm import Session

from backend.app.models import Order, OrderItem, Review, Sneaker
from backend.app.seed import SEED_SNEAKERS, seed_sneakers


def test_sqlite_foreign_key_enforcement_is_enabled(db_session: Session) -> None:
    foreign_keys_enabled = db_session.connection().exec_driver_sql(
        "PRAGMA foreign_keys"
    ).scalar()

    assert foreign_keys_enabled == 1


def test_seed_sneakers_is_idempotent(db_session: Session) -> None:
    initial_count = len(db_session.scalars(select(Sneaker)).all())

    inserted = seed_sneakers(db_session)
    final_count = len(db_session.scalars(select(Sneaker)).all())

    assert initial_count == 6
    assert inserted == 0
    assert final_count == initial_count


def test_seeded_catalog_contains_all_required_sneaker_data(db_session: Session) -> None:
    products = list(db_session.scalars(select(Sneaker).order_by(Sneaker.id)).all())

    assert len(products) == len(SEED_SNEAKERS)
    assert {product.name for product in products} == {
        sneaker["name"] for sneaker in SEED_SNEAKERS
    }

    for product in products:
        assert product.brand
        assert product.price > Decimal("0.00")
        assert product.currency == "EUR"
        assert product.short_description
        assert product.long_description
        assert product.image_url.startswith("/static/images/")
        assert product.sizes
        assert product.stock >= 0
        assert 0 <= product.rating <= 5


def test_sneaker_crud_roundtrip(db_session: Session) -> None:
    sneaker = Sneaker(
        name="Test Runner",
        brand="QA",
        price=Decimal("79.50"),
        currency="EUR",
        short_description="Short",
        long_description="Long",
        image_url="/static/images/test-runner.jpg",
        sizes=["41", "42"],
        color="Black",
        material="Mesh",
        stock=3,
        rating=4.0,
        is_new=True,
    )

    db_session.add(sneaker)
    db_session.commit()
    db_session.refresh(sneaker)

    loaded = db_session.get(Sneaker, sneaker.id)
    assert loaded is not None
    assert loaded.name == "Test Runner"

    loaded.stock = 2
    db_session.commit()
    db_session.refresh(loaded)
    assert loaded.stock == 2

    db_session.delete(loaded)
    db_session.commit()
    assert db_session.get(Sneaker, sneaker.id) is None


def test_negative_stock_violates_database_constraint(db_session: Session) -> None:
    db_session.add(
        Sneaker(
            name="Broken Stock",
            brand="QA",
            price=Decimal("10.00"),
            currency="EUR",
            short_description="Short",
            long_description="Long",
            image_url="/static/images/broken-stock.jpg",
            sizes=["42"],
            color="Black",
            material="Mesh",
            stock=-1,
            rating=3.0,
            is_new=False,
        )
    )

    with pytest.raises(exc.IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_negative_price_violates_database_constraint(db_session: Session) -> None:
    db_session.add(
        Sneaker(
            name="Broken Price",
            brand="QA",
            price=Decimal("-0.01"),
            currency="EUR",
            short_description="Short",
            long_description="Long",
            image_url="/static/images/broken-price.jpg",
            sizes=["42"],
            color="Black",
            material="Mesh",
            stock=1,
            rating=3.0,
            is_new=False,
        )
    )

    with pytest.raises(exc.IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_sneaker_rating_outside_allowed_range_violates_database_constraint(
    db_session: Session,
) -> None:
    db_session.add(
        Sneaker(
            name="Broken Rating",
            brand="QA",
            price=Decimal("10.00"),
            currency="EUR",
            short_description="Short",
            long_description="Long",
            image_url="/static/images/broken-rating.jpg",
            sizes=["42"],
            color="Black",
            material="Mesh",
            stock=1,
            rating=5.1,
            is_new=False,
        )
    )

    with pytest.raises(exc.IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_review_rating_outside_allowed_range_violates_database_constraint(
    db_session: Session,
) -> None:
    product = db_session.get(Sneaker, 1)
    assert product is not None

    db_session.add(
        Review(
            product_id=product.id,
            author="QA",
            rating=0,
            comment="Invalid rating",
        )
    )

    with pytest.raises(exc.IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_review_rejects_unknown_product_foreign_key(db_session: Session) -> None:
    db_session.add(
        Review(
            product_id=9999,
            author="QA",
            rating=4,
            comment="Product does not exist",
        )
    )

    with pytest.raises(exc.IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_review_crud_roundtrip(db_session: Session) -> None:
    product = db_session.get(Sneaker, 1)
    assert product is not None

    review = Review(
        product_id=product.id,
        author="QA",
        rating=4,
        comment="Initial comment",
    )
    db_session.add(review)
    db_session.commit()
    db_session.refresh(review)

    loaded = db_session.get(Review, review.id)
    assert loaded is not None
    assert loaded.comment == "Initial comment"

    loaded.comment = "Updated comment"
    loaded.rating = 5
    db_session.commit()
    db_session.refresh(loaded)
    assert loaded.comment == "Updated comment"
    assert loaded.rating == 5

    db_session.delete(loaded)
    db_session.commit()
    assert db_session.get(Review, review.id) is None


def test_order_crud_with_items_and_delete_cascades(db_session: Session) -> None:
    product = db_session.get(Sneaker, 1)
    assert product is not None

    order = Order(
        status="created",
        shipping_name="Ada Lovelace",
        shipping_street="Teststrasse 1",
        shipping_zip="10115",
        shipping_city="Berlin",
        shipping_country="Germany",
        email="ada@example.com",
        payment_method="credit_card",
        subtotal=Decimal("129.99"),
        total=Decimal("129.99"),
        items=[
            OrderItem(
                product_id=product.id,
                name_snapshot=product.name,
                brand_snapshot=product.brand,
                price_snapshot=product.price,
                image_url_snapshot=product.image_url,
                size="42",
                quantity=1,
                line_total=product.price,
            )
        ],
    )
    db_session.add(order)
    db_session.commit()

    saved_order = db_session.get(Order, order.id)
    assert saved_order is not None
    assert len(saved_order.items) == 1
    assert saved_order.items[0].product_id == product.id
    item_id = saved_order.items[0].id

    db_session.delete(saved_order)
    db_session.commit()

    assert db_session.get(Order, order.id) is None
    assert db_session.get(OrderItem, item_id) is None


def test_order_item_rejects_unknown_product_foreign_key(db_session: Session) -> None:
    order = Order(
        status="created",
        shipping_name="Ada Lovelace",
        shipping_street="Teststrasse 1",
        shipping_zip="10115",
        shipping_city="Berlin",
        shipping_country="Germany",
        email="ada@example.com",
        payment_method="credit_card",
        subtotal=Decimal("10.00"),
        total=Decimal("10.00"),
        items=[
            OrderItem(
                product_id=9999,
                name_snapshot="Missing Product",
                brand_snapshot="QA",
                price_snapshot=Decimal("10.00"),
                image_url_snapshot="/static/images/missing.jpg",
                size="42",
                quantity=1,
                line_total=Decimal("10.00"),
            )
        ],
    )

    db_session.add(order)
    with pytest.raises(exc.IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_deleting_ordered_sneaker_is_restricted(db_session: Session) -> None:
    product = db_session.get(Sneaker, 1)
    assert product is not None
    product_id = product.id

    order = Order(
        status="created",
        shipping_name="Ada Lovelace",
        shipping_street="Teststrasse 1",
        shipping_zip="10115",
        shipping_city="Berlin",
        shipping_country="Germany",
        email="ada@example.com",
        payment_method="credit_card",
        subtotal=product.price,
        total=product.price,
        items=[
            OrderItem(
                product_id=product.id,
                name_snapshot=product.name,
                brand_snapshot=product.brand,
                price_snapshot=product.price,
                image_url_snapshot=product.image_url,
                size="42",
                quantity=1,
                line_total=product.price,
            )
        ],
    )
    db_session.add(order)
    db_session.commit()

    db_session.delete(product)
    with pytest.raises(exc.IntegrityError):
        db_session.commit()

    db_session.rollback()
    assert db_session.get(Sneaker, product_id) is not None


def test_order_item_quantity_must_be_positive(db_session: Session) -> None:
    product = db_session.get(Sneaker, 1)
    assert product is not None

    order = Order(
        status="created",
        shipping_name="Ada Lovelace",
        shipping_street="Teststrasse 1",
        shipping_zip="10115",
        shipping_city="Berlin",
        shipping_country="Germany",
        email="ada@example.com",
        payment_method="credit_card",
        subtotal=Decimal("0.00"),
        total=Decimal("0.00"),
        items=[
            OrderItem(
                product_id=product.id,
                name_snapshot=product.name,
                brand_snapshot=product.brand,
                price_snapshot=product.price,
                image_url_snapshot=product.image_url,
                size="42",
                quantity=0,
                line_total=Decimal("0.00"),
            )
        ],
    )

    db_session.add(order)
    with pytest.raises(exc.IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_order_negative_total_violates_database_constraint(db_session: Session) -> None:
    db_session.add(
        Order(
            status="created",
            shipping_name="Ada Lovelace",
            shipping_street="Teststrasse 1",
            shipping_zip="10115",
            shipping_city="Berlin",
            shipping_country="Germany",
            email="ada@example.com",
            payment_method="credit_card",
            subtotal=Decimal("10.00"),
            total=Decimal("-0.01"),
        )
    )

    with pytest.raises(exc.IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_deleting_sneaker_cascades_reviews(db_session: Session) -> None:
    product = db_session.get(Sneaker, 2)
    assert product is not None

    review = Review(product_id=product.id, author="QA", rating=5, comment="Great")
    db_session.add(review)
    db_session.commit()

    assert len(product.reviews) == 1

    db_session.delete(product)
    db_session.commit()

    assert db_session.get(Review, review.id) is None
