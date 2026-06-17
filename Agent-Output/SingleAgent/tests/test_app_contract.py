import asyncio
import json

from starlette.requests import Request


FORBIDDEN_UI_WORDS = ("FastAPI", "Backend", "API", "Swagger", "/docs", "uvicorn", "Traceback")


def test_frontend_is_served_with_branding(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "SneakerHaus" in response.text
    assert "Sneaker, die bewegen." in response.text
    for word in FORBIDDEN_UI_WORDS:
        assert word not in response.text


def test_documentation_routes_are_not_public(client):
    for path in ("/docs", "/redoc", "/openapi.json"):
        response = client.get(path)
        assert response.status_code == 404
        assert response.json() == {
            "error": {
                "code": "404",
                "message": "Not Found",
            }
        }


def test_http_exception_uses_public_error_shape(client):
    response = client.get("/api/products/9999")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "404",
            "message": "Dieses Produkt ist leider nicht mehr verfuegbar.",
        }
    }


def test_validation_exception_uses_public_error_shape(client):
    response = client.post(
        "/api/cart/items",
        json={"product_id": 1, "size": 42, "quantity": 0},
    )

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "validation_error",
            "message": "Bitte pruefe deine Eingaben.",
        }
    }


def test_unhandled_exception_uses_safe_public_message(client):
    request = Request({"type": "http", "method": "GET", "path": "/api/test-broken", "headers": []})
    handler = client.app.exception_handlers[Exception]
    response = asyncio.run(handler(request, RuntimeError("database credentials should never leak")))

    assert response.status_code == 500
    assert json.loads(response.body) == {
        "error": {
            "code": "internal_error",
            "message": "Es ist ein Fehler aufgetreten.",
        }
    }
    assert b"database credentials" not in response.body
