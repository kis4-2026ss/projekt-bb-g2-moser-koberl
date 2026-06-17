from decimal import Decimal


def test_seeded_products_are_complete_and_unique(client):
    response = client.get("/api/products")

    assert response.status_code == 200
    products = response.json()
    assert len(products) >= 8
    assert len({product["image_url"] for product in products}) == len(products)
    assert {product["brand"] for product in products} >= {
        "Nike",
        "Adidas",
        "New Balance",
        "Puma",
        "Asics",
        "Reebok",
        "Converse",
    }
    for product in products:
        assert product["currency"] == "EUR"
        assert Decimal(str(product["price"])) > Decimal("50.00")
        assert 0 <= float(product["rating"]) <= 5
        assert product["image_url"].startswith("https://")
        assert product["short_description"]


def test_products_support_brand_and_search_filters(client):
    brand_response = client.get("/api/products", params={"brand": "nike"})
    search_response = client.get("/api/products", params={"search": "runner"})

    assert brand_response.status_code == 200
    assert [product["brand"] for product in brand_response.json()] == ["Nike"]
    assert search_response.status_code == 200
    assert all(
        "runner" in f"{product['name']} {product['short_description']}".lower()
        for product in search_response.json()
    )


def test_product_detail_contains_all_required_fields(client):
    response = client.get("/api/products/1")

    assert response.status_code == 200
    product = response.json()
    assert product["name"] == "Air Pulse Runner"
    assert product["long_description"]
    assert product["sizes"] == [40, 41, 42, 43, 44, 45]
    assert product["color"]
    assert product["material"]
    assert isinstance(product["stock"], int)
    assert product["stock"] > 0


def test_reviews_can_be_listed_and_created_with_recalculated_rating(client):
    before = client.get("/api/products/1/reviews").json()

    create_response = client.post(
        "/api/products/1/reviews",
        json={"author": None, "rating": 3, "comment": "Solide Verarbeitung und bequem."},
    )
    after = client.get("/api/products/1/reviews").json()
    product = client.get("/api/products/1").json()

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["author"] == "Gast"
    assert created["rating"] == 3
    assert created["comment"] == "Solide Verarbeitung und bequem."
    assert after["count"] == before["count"] + 1
    assert after["reviews"][0]["id"] == created["id"]
    assert after["average_rating"] == product["rating"]


def test_review_validation_and_unknown_product_errors(client):
    invalid = client.post("/api/products/1/reviews", json={"rating": 6, "comment": "ungueltig"})
    missing_get = client.get("/api/products/999/reviews")
    missing_post = client.post(
        "/api/products/999/reviews",
        json={"author": "Mara", "rating": 5, "comment": "Guter Schuh."},
    )

    assert invalid.status_code == 400
    assert invalid.json()["error"]["code"] == "validation_error"
    assert missing_get.status_code == 404
    assert missing_get.json()["error"]["message"] == "Dieses Produkt ist leider nicht mehr verfuegbar."
    assert missing_post.status_code == 404
