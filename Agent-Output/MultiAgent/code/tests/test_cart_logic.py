from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from backend.app.api import cart as cart_api
from backend.app.api.cart import StoredCartItem, build_cart_response
from backend.app.schemas import CartItemCreate


def test_build_cart_response_calculates_subtotal_and_line_totals(
    db_session: Session,
) -> None:
    cart_api._cart_items[1] = StoredCartItem(
        item_id=1,
        product_id=1,
        size="42",
        quantity=2,
    )
    cart_api._cart_items[2] = StoredCartItem(
        item_id=2,
        product_id=3,
        size="41",
        quantity=1,
    )

    cart = build_cart_response(db_session)

    assert len(cart.items) == 2
    assert cart.items[0].line_total == Decimal("259.98")
    assert cart.items[1].line_total == Decimal("89.90")
    assert cart.subtotal == Decimal("349.88")
    assert cart.total == Decimal("349.88")


def test_build_cart_response_skips_removed_products(db_session: Session) -> None:
    cart_api._cart_items[1] = StoredCartItem(
        item_id=1,
        product_id=9999,
        size="42",
        quantity=2,
    )

    cart = build_cart_response(db_session)

    assert cart.items == []
    assert cart.subtotal == Decimal("0.00")
    assert cart.total == Decimal("0.00")


def test_clear_cart_removes_all_stored_items() -> None:
    cart_api._cart_items[1] = StoredCartItem(
        item_id=1,
        product_id=1,
        size="42",
        quantity=2,
    )

    cart_api.clear_cart()

    assert cart_api.get_stored_cart_items() == []


def test_add_cart_item_combines_same_product_and_size(db_session: Session) -> None:
    first_item = cart_api.add_cart_item(
        CartItemCreate(product_id=1, size="42", quantity=1),
        db_session,
    )
    second_item = cart_api.add_cart_item(
        CartItemCreate(product_id=1, size="42", quantity=2),
        db_session,
    )

    assert second_item.item_id == first_item.item_id
    assert second_item.quantity == 3
    assert second_item.line_total == Decimal("389.97")


def test_add_cart_item_keeps_different_sizes_separate(db_session: Session) -> None:
    first_item = cart_api.add_cart_item(
        CartItemCreate(product_id=1, size="41", quantity=1),
        db_session,
    )
    second_item = cart_api.add_cart_item(
        CartItemCreate(product_id=1, size="42", quantity=1),
        db_session,
    )

    cart = cart_api.build_cart_response(db_session)

    assert first_item.item_id != second_item.item_id
    assert len(cart.items) == 2
    assert cart.subtotal == Decimal("259.98")


def test_add_cart_item_keeps_same_product_with_different_sizes_in_separate_totals(
    db_session: Session,
) -> None:
    cart_api.add_cart_item(
        CartItemCreate(product_id=1, size="41", quantity=2),
        db_session,
    )
    cart_api.add_cart_item(
        CartItemCreate(product_id=1, size="42", quantity=3),
        db_session,
    )

    cart = cart_api.build_cart_response(db_session)

    assert [item.quantity for item in cart.items] == [2, 3]
    assert [item.line_total for item in cart.items] == [
        Decimal("259.98"),
        Decimal("389.97"),
    ]
    assert cart.subtotal == Decimal("649.95")


def test_add_cart_item_validates_combined_quantity_against_stock(
    db_session: Session,
) -> None:
    cart_api.add_cart_item(
        CartItemCreate(product_id=6, size="42", quantity=10),
        db_session,
    )

    with pytest.raises(cart_api.HTTPException) as error:
        cart_api.add_cart_item(
            CartItemCreate(product_id=6, size="42", quantity=10),
            db_session,
        )

    assert error.value.status_code == 400
    assert error.value.detail == "Requested quantity exceeds available stock"


def test_update_cart_item_revalidates_current_catalog_size(
    db_session: Session,
) -> None:
    item = cart_api.add_cart_item(
        CartItemCreate(product_id=1, size="42", quantity=1),
        db_session,
    )
    product = db_session.get(cart_api.Sneaker, 1)
    assert product is not None
    product.sizes = ["39", "40", "41"]
    db_session.commit()

    with pytest.raises(cart_api.HTTPException) as error:
        cart_api.update_cart_item(
            item.item_id,
            cart_api.CartItemUpdate(quantity=2),
            db_session,
        )

    assert error.value.status_code == 400
    assert error.value.detail == "Selected size is not available for this product"

    cart = cart_api.build_cart_response(db_session)
    assert cart.items[0].quantity == 1


def test_failed_update_above_stock_keeps_existing_cart_quantity(
    db_session: Session,
) -> None:
    item = cart_api.add_cart_item(
        CartItemCreate(product_id=6, size="42", quantity=3),
        db_session,
    )

    with pytest.raises(cart_api.HTTPException) as error:
        cart_api.update_cart_item(
            item.item_id,
            cart_api.CartItemUpdate(quantity=20),
            db_session,
        )

    assert error.value.status_code == 400
    assert error.value.detail == "Requested quantity exceeds available stock"

    cart = cart_api.build_cart_response(db_session)
    assert len(cart.items) == 1
    assert cart.items[0].quantity == 3
    assert cart.items[0].line_total == Decimal("419.85")
    assert cart.subtotal == Decimal("419.85")


def test_failed_combined_quantity_add_keeps_existing_cart_quantity(
    db_session: Session,
) -> None:
    cart_api.add_cart_item(
        CartItemCreate(product_id=6, size="42", quantity=10),
        db_session,
    )

    with pytest.raises(cart_api.HTTPException):
        cart_api.add_cart_item(
            CartItemCreate(product_id=6, size="42", quantity=10),
            db_session,
        )

    cart = cart_api.build_cart_response(db_session)

    assert len(cart.items) == 1
    assert cart.items[0].quantity == 10
    assert cart.items[0].line_total == Decimal("1399.50")
    assert cart.subtotal == Decimal("1399.50")
