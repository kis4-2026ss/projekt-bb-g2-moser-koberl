from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "frontend"
COMPONENT_DIR = FRONTEND_DIR / "components"


def read_frontend_file(relative_path: str) -> str:
    return (FRONTEND_DIR / relative_path).read_text(encoding="utf-8")


def read_component(filename: str) -> str:
    return (COMPONENT_DIR / filename).read_text(encoding="utf-8")


def test_index_declares_mobile_viewport_and_global_stylesheet() -> None:
    index = read_frontend_file("index.html")

    assert '<meta name="viewport" content="width=device-width, initial-scale=1" />' in index
    assert '<link rel="stylesheet" href="/styles/app.css" />' in index
    assert '<body class="bg-zinc-50 text-zinc-950 antialiased">' in index


def test_global_css_prevents_common_mobile_overflow_sources() -> None:
    css = read_frontend_file("styles/app.css")

    assert "min-height: 100vh;" in css
    assert "* {\n  min-width: 0;\n}" in css
    assert "img {\n  max-width: 100%;\n}" in css
    assert "button,\ninput,\nselect,\ntextarea" in css
    assert ".focus-ring:focus-visible" in css


def test_catalog_page_uses_responsive_filter_and_product_grids() -> None:
    source = read_component("product-list.js")

    assert "grid gap-4 md:grid-cols-[1.3fr_0.7fr] md:items-end" in source
    assert "grid gap-3 sm:grid-cols-[1fr_auto] md:justify-end" in source
    assert "w-full rounded-md border border-zinc-300 bg-white px-3 py-2 md:w-64" in source
    assert "grid gap-5 sm:grid-cols-2 lg:grid-cols-3" in source
    assert "text-3xl font-bold tracking-normal text-zinc-950 sm:text-4xl md:text-5xl" in source


def test_cart_and_checkout_promote_sidebar_only_on_large_screens() -> None:
    cart_source = read_component("shopping-cart.js")
    checkout_source = read_component("checkout-page.js")

    assert "grid gap-8 lg:grid-cols-[1fr_360px]" in cart_source
    assert "grid gap-8 lg:grid-cols-[1fr_360px]" in checkout_source
    assert "sm:grid-cols-[120px_1fr_auto]" in cart_source
    assert "h-28 w-full rounded-md bg-zinc-100 object-cover sm:w-28" in cart_source
    assert "flex items-center gap-2 sm:flex-col sm:items-end" in cart_source


def test_checkout_form_fields_stack_on_mobile_and_split_on_wider_viewports() -> None:
    source = read_component("checkout-page.js")

    assert "grid gap-4 sm:grid-cols-2" in source
    assert 'this.input("street", "Strasse", "text", "sm:col-span-2")' in source
    assert 'class="focus-ring mt-6 w-full rounded-md bg-zinc-950 px-5 py-3 font-bold text-white hover:bg-zinc-800 sm:w-auto"' in source
    assert 'class="min-w-0 break-words"' in source
    assert 'class="shrink-0"' in source
