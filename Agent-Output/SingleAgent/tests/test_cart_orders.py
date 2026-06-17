def shipping_payload(email="max@example.de"):
    return {
        "name": "Max Mustermann",
        "street": "Hausweg 12",
        "zip": "10115",
        "city": "Berlin",
        "country": "Deutschland",
        "email": email,
    }


def test_cart_starts_empty_and_sets_session_cookie(client):
    response = client.get("/api/cart")

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "item_count": 0,
        "subtotal": "0.00",
        "total": "0.00",
    }
    assert "sneakerhaus_session" in response.headers["set-cookie"]


def test_cart_add_merges_same_product_size_and_calculates_totals(client):
    first = client.post("/api/cart/items", json={"product_id": 1, "size": 42, "quantity": 1})
    second = client.post("/api/cart/items", json={"product_id": 1, "size": 42, "quantity": 2})

    assert first.status_code == 201
    assert second.status_code == 201
    cart = second.json()
    assert cart["item_count"] == 3
    assert len(cart["items"]) == 1
    assert cart["items"][0]["quantity"] == 3
    assert cart["items"][0]["name"] == "Air Pulse Runner"
    assert cart["items"][0]["line_total"] == "389.70"
    assert cart["subtotal"] == "389.70"
    assert cart["total"] == cart["subtotal"]


def test_cart_update_and_delete_item(client):
    cart = client.post("/api/cart/items", json={"product_id": 2, "size": 41, "quantity": 1}).json()
    item_id = cart["items"][0]["id"]

    updated = client.patch(f"/api/cart/items/{item_id}", json={"quantity": 4})
    deleted = client.delete(f"/api/cart/items/{item_id}")
    empty = client.get("/api/cart")

    assert updated.status_code == 200
    assert updated.json()["item_count"] == 4
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert empty.json()["item_count"] == 0


def test_cart_rejects_unknown_product_size_stock_and_item(client):
    unknown = client.post("/api/cart/items", json={"product_id": 999, "size": 42, "quantity": 1})
    bad_size = client.post("/api/cart/items", json={"product_id": 1, "size": 99, "quantity": 1})
    too_many = client.post("/api/cart/items", json={"product_id": 1, "size": 42, "quantity": 999})
    missing_patch = client.patch("/api/cart/items/999", json={"quantity": 1})
    missing_delete = client.delete("/api/cart/items/999")

    assert unknown.status_code == 404
    assert bad_size.status_code == 400
    assert bad_size.json()["error"]["message"] == "Diese Groesse ist aktuell nicht verfuegbar."
    assert too_many.status_code == 400
    assert too_many.json()["error"]["message"] == "Die gewuenschte Menge ist aktuell nicht verfuegbar."
    assert missing_patch.status_code == 404
    assert missing_delete.status_code == 404


def test_order_requires_non_empty_cart_and_valid_shipping(client):
    empty = client.post(
        "/api/orders",
        json={"shipping": shipping_payload(), "payment_method": "invoice"},
    )
    client.post("/api/cart/items", json={"product_id": 1, "size": 42, "quantity": 1})
    invalid_email = client.post(
        "/api/orders",
        json={"shipping": shipping_payload(email="keine-mail"), "payment_method": "invoice"},
    )
    invalid_payment = client.post(
        "/api/orders",
        json={"shipping": shipping_payload(), "payment_method": "cash"},
    )

    assert empty.status_code == 400
    assert empty.json()["error"]["message"] == "Dein Warenkorb ist leer."
    assert invalid_email.status_code == 400
    assert invalid_email.json()["error"]["code"] == "validation_error"
    assert invalid_payment.status_code == 400
    assert invalid_payment.json()["error"]["code"] == "validation_error"


def test_checkout_creates_order_snapshots_and_clears_cart(client):
    client.post("/api/cart/items", json={"product_id": 1, "size": 42, "quantity": 2})
    client.post("/api/cart/items", json={"product_id": 3, "size": 43, "quantity": 1})

    created = client.post(
        "/api/orders",
        json={"shipping": shipping_payload(), "payment_method": "credit_card_demo"},
    )
    empty_cart = client.get("/api/cart").json()
    fetched = client.get(f"/api/orders/{created.json()['order_id']}")

    assert created.status_code == 201
    order = created.json()
    assert order["status"] == "confirmed"
    assert order["shipping"] == shipping_payload()
    assert order["payment_method"] == "credit_card_demo"
    assert len(order["items"]) == 2
    assert order["subtotal"] == "379.70"
    assert order["total"] == "379.70"
    assert order["items"][0]["name"] == "Air Pulse Runner"
    assert order["items"][0]["brand"] == "Nike"
    assert empty_cart["item_count"] == 0
    assert fetched.status_code == 200
    assert fetched.json() == order


def test_unknown_order_returns_friendly_not_found(client):
    response = client.get("/api/orders/999")

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "Diese Bestellung wurde nicht gefunden."
