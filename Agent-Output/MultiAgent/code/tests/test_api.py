from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models import Sneaker


def valid_order_payload() -> dict[str, object]:
    return {
        "shipping": {
            "name": "Ada Lovelace",
            "street": "Teststrasse 1",
            "zip": "10115",
            "city": "Berlin",
            "country": "Germany",
            "email": "ada@example.com",
        },
        "payment_method": "credit_card",
    }


def test_health_endpoint_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_products_endpoint_returns_seeded_catalog(client: TestClient) -> None:
    response = client.get("/api/products")

    assert response.status_code == 200
    products = response.json()
    assert len(products) == 6
    assert products[0]["name"] == "Air Zoom Pulse"
    assert products[0]["price"] == 129.99


def test_product_detail_returns_seeded_product(client: TestClient) -> None:
    response = client.get("/api/products/1")

    assert response.status_code == 200
    product = response.json()
    assert product["id"] == 1
    assert product["name"] == "Air Zoom Pulse"
    assert product["sizes"] == ["39", "40", "41", "42", "43", "44", "45"]


def test_product_detail_returns_404_for_unknown_product(client: TestClient) -> None:
    response = client.get("/api/products/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_cart_rejects_unknown_product(client: TestClient) -> None:
    response = client.post(
        "/api/cart/items",
        json={"product_id": 9999, "size": "42", "quantity": 1},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_cart_rejects_unavailable_size(client: TestClient) -> None:
    response = client.post(
        "/api/cart/items",
        json={"product_id": 1, "size": "99", "quantity": 1},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Selected size is not available for this product"


def test_cart_rejects_quantity_above_stock(client: TestClient) -> None:
    response = client.post(
        "/api/cart/items",
        json={"product_id": 6, "size": "42", "quantity": 20},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Requested quantity exceeds available stock"


def test_cart_update_rejects_quantity_above_stock(client: TestClient) -> None:
    add_response = client.post(
        "/api/cart/items",
        json={"product_id": 6, "size": "42", "quantity": 1},
    )
    assert add_response.status_code == 201
    item_id = add_response.json()["item_id"]

    response = client.patch(
        f"/api/cart/items/{item_id}",
        json={"quantity": 20},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Requested quantity exceeds available stock"


def test_cart_rejects_invalid_quantity_payload(client: TestClient) -> None:
    response = client.post(
        "/api/cart/items",
        json={"product_id": 1, "size": "42", "quantity": 0},
    )

    assert response.status_code == 422


def test_cart_update_rejects_invalid_quantity_payload(client: TestClient) -> None:
    add_response = client.post(
        "/api/cart/items",
        json={"product_id": 1, "size": "42", "quantity": 1},
    )
    assert add_response.status_code == 201
    item_id = add_response.json()["item_id"]

    response = client.patch(
        f"/api/cart/items/{item_id}",
        json={"quantity": 0},
    )

    assert response.status_code == 422


def test_cart_starts_empty(client: TestClient) -> None:
    response = client.get("/api/cart")

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "subtotal": 0.0,
        "total": 0.0,
        "currency": "EUR",
    }


def test_cart_api_combines_same_product_and_size(client: TestClient) -> None:
    first_response = client.post(
        "/api/cart/items",
        json={"product_id": 1, "size": "42", "quantity": 1},
    )
    second_response = client.post(
        "/api/cart/items",
        json={"product_id": 1, "size": "42", "quantity": 2},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert second_response.json()["item_id"] == first_response.json()["item_id"]
    assert second_response.json()["quantity"] == 3

    cart_response = client.get("/api/cart")
    assert cart_response.status_code == 200
    cart = cart_response.json()
    assert len(cart["items"]) == 1
    assert cart["subtotal"] == 389.97


def test_cart_item_can_be_updated_and_deleted(client: TestClient) -> None:
    add_response = client.post(
        "/api/cart/items",
        json={"product_id": 1, "size": "42", "quantity": 1},
    )
    assert add_response.status_code == 201
    item_id = add_response.json()["item_id"]

    update_response = client.patch(
        f"/api/cart/items/{item_id}",
        json={"quantity": 3},
    )
    assert update_response.status_code == 204

    cart_response = client.get("/api/cart")
    assert cart_response.status_code == 200
    cart = cart_response.json()
    assert cart["items"][0]["quantity"] == 3
    assert cart["items"][0]["line_total"] == 389.97
    assert cart["subtotal"] == 389.97

    delete_response = client.delete(f"/api/cart/items/{item_id}")
    assert delete_response.status_code == 204

    empty_cart_response = client.get("/api/cart")
    assert empty_cart_response.status_code == 200
    assert empty_cart_response.json()["items"] == []


def test_cart_delete_returns_404_for_unknown_item(client: TestClient) -> None:
    response = client.delete("/api/cart/items/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Cart item not found"


def test_cart_update_returns_404_for_unknown_item(client: TestClient) -> None:
    response = client.patch("/api/cart/items/9999", json={"quantity": 2})

    assert response.status_code == 404
    assert response.json()["detail"] == "Cart item not found"


def test_cart_and_order_happy_path_persists_order_and_clears_cart(
    client: TestClient,
) -> None:
    cart_response = client.post(
        "/api/cart/items",
        json={"product_id": 1, "size": "42", "quantity": 2},
    )
    assert cart_response.status_code == 201
    assert cart_response.json()["line_total"] == 259.98

    order_response = client.post(
        "/api/orders",
        json=valid_order_payload(),
    )

    assert order_response.status_code == 201
    created_order = order_response.json()
    assert created_order["status"] == "created"
    assert created_order["total"] == 259.98

    persisted_response = client.get(f"/api/orders/{created_order['order_id']}")
    assert persisted_response.status_code == 200
    persisted_order = persisted_response.json()
    assert persisted_order["subtotal"] == 259.98
    assert persisted_order["items"][0]["name_snapshot"] == "Air Zoom Pulse"
    assert persisted_order["items"][0]["quantity"] == 2

    product_response = client.get("/api/products/1")
    assert product_response.status_code == 200
    assert product_response.json()["stock"] == 32

    empty_cart_response = client.get("/api/cart")
    assert empty_cart_response.status_code == 200
    assert empty_cart_response.json() == {
        "items": [],
        "subtotal": 0.0,
        "total": 0.0,
        "currency": "EUR",
    }


def test_multi_item_order_calculates_totals_and_deducts_each_product_stock(
    client: TestClient,
) -> None:
    first_cart_response = client.post(
        "/api/cart/items",
        json={"product_id": 1, "size": "42", "quantity": 2},
    )
    second_cart_response = client.post(
        "/api/cart/items",
        json={"product_id": 3, "size": "41", "quantity": 1},
    )
    assert first_cart_response.status_code == 201
    assert second_cart_response.status_code == 201

    order_response = client.post("/api/orders", json=valid_order_payload())

    assert order_response.status_code == 201
    created_order = order_response.json()
    assert created_order["total"] == 349.88

    persisted_response = client.get(f"/api/orders/{created_order['order_id']}")
    assert persisted_response.status_code == 200
    persisted_order = persisted_response.json()
    assert persisted_order["subtotal"] == 349.88
    assert persisted_order["total"] == 349.88
    assert [
        (item["product_id"], item["quantity"], item["line_total"])
        for item in persisted_order["items"]
    ] == [(1, 2, 259.98), (3, 1, 89.9)]

    first_product_response = client.get("/api/products/1")
    second_product_response = client.get("/api/products/3")
    assert first_product_response.status_code == 200
    assert second_product_response.status_code == 200
    assert first_product_response.json()["stock"] == 32
    assert second_product_response.json()["stock"] == 47

    cart_response = client.get("/api/cart")
    assert cart_response.status_code == 200
    assert cart_response.json()["items"] == []


def test_order_creation_rejects_empty_cart(client: TestClient) -> None:
    response = client.post(
        "/api/orders",
        json=valid_order_payload(),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Cart is empty"


def test_order_creation_rejects_cart_quantity_when_stock_changed(
    client: TestClient,
    db_session: Session,
) -> None:
    add_response = client.post(
        "/api/cart/items",
        json={"product_id": 1, "size": "42", "quantity": 2},
    )
    assert add_response.status_code == 201

    product = db_session.get(Sneaker, 1)
    assert product is not None
    product.stock = 1
    db_session.commit()

    response = client.post(
        "/api/orders",
        json={
            "shipping": {
                "name": "Ada Lovelace",
                "street": "Teststrasse 1",
                "zip": "10115",
                "city": "Berlin",
                "country": "Germany",
                "email": "ada@example.com",
            },
            "payment_method": "credit_card",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Cart quantity exceeds available stock"

    cart_response = client.get("/api/cart")
    assert cart_response.status_code == 200
    cart = cart_response.json()
    assert len(cart["items"]) == 1
    assert cart["items"][0]["quantity"] == 2


def test_order_creation_rejects_cart_product_removed_after_add(
    client: TestClient,
    db_session: Session,
) -> None:
    add_response = client.post(
        "/api/cart/items",
        json={"product_id": 1, "size": "42", "quantity": 1},
    )
    assert add_response.status_code == 201

    product = db_session.get(Sneaker, 1)
    assert product is not None
    db_session.delete(product)
    db_session.commit()

    response = client.post(
        "/api/orders",
        json={
            "shipping": {
                "name": "Ada Lovelace",
                "street": "Teststrasse 1",
                "zip": "10115",
                "city": "Berlin",
                "country": "Germany",
                "email": "ada@example.com",
            },
            "payment_method": "credit_card",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Cart contains an unavailable product"


def test_order_creation_rejects_cart_size_removed_after_add(
    client: TestClient,
    db_session: Session,
) -> None:
    add_response = client.post(
        "/api/cart/items",
        json={"product_id": 1, "size": "42", "quantity": 1},
    )
    assert add_response.status_code == 201

    product = db_session.get(Sneaker, 1)
    assert product is not None
    product.sizes = ["39", "40", "41"]
    db_session.commit()

    response = client.post(
        "/api/orders",
        json={
            "shipping": {
                "name": "Ada Lovelace",
                "street": "Teststrasse 1",
                "zip": "10115",
                "city": "Berlin",
                "country": "Germany",
                "email": "ada@example.com",
            },
            "payment_method": "credit_card",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Cart contains an unavailable product size"


def test_order_creation_rejects_invalid_shipping_email(client: TestClient) -> None:
    client.post(
        "/api/cart/items",
        json={"product_id": 1, "size": "42", "quantity": 1},
    )

    response = client.post(
        "/api/orders",
        json={
            "shipping": {
                "name": "Ada Lovelace",
                "street": "Teststrasse 1",
                "zip": "10115",
                "city": "Berlin",
                "country": "Germany",
                "email": "not-an-email",
            },
            "payment_method": "credit_card",
        },
    )

    assert response.status_code == 422


def test_order_detail_returns_404_for_unknown_order(client: TestClient) -> None:
    response = client.get("/api/orders/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


def test_reviews_happy_path_updates_product_average_rating(client: TestClient) -> None:
    first_response = client.post(
        "/api/products/1/reviews",
        json={"author": "QA", "rating": 5, "comment": "Excellent"},
    )
    second_response = client.post(
        "/api/products/1/reviews",
        json={"author": "QA", "rating": 3, "comment": "Okay"},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    reviews_response = client.get("/api/products/1/reviews")
    assert reviews_response.status_code == 200
    reviews = reviews_response.json()
    assert reviews["average_rating"] == 4.0
    assert [review["rating"] for review in reviews["reviews"]] == [3, 5]

    product_response = client.get("/api/products/1")
    assert product_response.status_code == 200
    assert product_response.json()["rating"] == 4.0


def test_review_listing_returns_empty_collection_for_unreviewed_product(
    client: TestClient,
) -> None:
    response = client.get("/api/products/2/reviews")

    assert response.status_code == 200
    assert response.json() == {"average_rating": 0.0, "reviews": []}


def test_review_listing_returns_404_for_unknown_product(client: TestClient) -> None:
    response = client.get("/api/products/9999/reviews")

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_review_creation_rejects_invalid_rating(client: TestClient) -> None:
    response = client.post(
        "/api/products/1/reviews",
        json={"author": "QA", "rating": 6, "comment": "Too high"},
    )

    assert response.status_code == 422


def test_review_creation_returns_404_for_unknown_product(client: TestClient) -> None:
    response = client.post(
        "/api/products/9999/reviews",
        json={"author": "QA", "rating": 5, "comment": "No product"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"
