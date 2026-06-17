from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = ROOT / "frontend" / "components"


def read_frontend_file(relative_path):
    return (ROOT / "frontend" / relative_path).read_text(encoding="utf-8")


def test_index_contains_branding_and_global_shell():
    html = read_frontend_file("index.html")

    assert "<title>SneakerHaus - Sneaker, die bewegen.</title>" in html
    assert "<site-header></site-header>" in html
    assert "<site-footer></site-footer>" in html
    assert 'src="/components/app.js"' in html
    assert "animate-pulse" not in html


def test_hash_router_declares_all_required_routes():
    source = read_frontend_file("components/app.js")

    for route in (
        "#/",
        "#/cart",
        "#/checkout",
        "#/legal/imprint",
        "#/legal/terms",
        "#/legal/contact",
    ):
        assert route in source
    assert "product-detail" in source
    assert "order-confirmation" in source
    assert "not-found" in source


def test_required_web_components_are_defined():
    component_sources = "\n".join(path.read_text(encoding="utf-8") for path in COMPONENTS.glob("*.js"))

    for component in (
        "site-header",
        "site-footer",
        "product-list",
        "product-detail",
        "shopping-cart",
        "checkout-page",
        "order-confirmation",
        "imprint-page",
        "terms-page",
        "contact-page",
        "not-found",
    ):
        assert f'customElements.define("{component}"' in component_sources


def test_frontend_uses_skeletons_and_friendly_copy():
    api_source = read_frontend_file("components/api.js")
    detail_source = read_frontend_file("components/product-detail.js")
    cart_source = read_frontend_file("components/cart.js")
    checkout_source = read_frontend_file("components/checkout.js")

    assert "animate-pulse" in api_source
    assert "Lade" not in api_source
    assert "Dieses Produkt ist leider nicht mehr verfuegbar." in detail_source
    assert "Dein Warenkorb ist leer." in cart_source
    assert "Jetzt kaufen" in checkout_source
