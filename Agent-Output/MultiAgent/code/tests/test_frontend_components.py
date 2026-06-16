import subprocess
import textwrap
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMPONENT_DIR = PROJECT_ROOT / "frontend" / "components"

EXPECTED_COMPONENTS = {
    "product-list.js": "product-list",
    "product-detail.js": "product-detail",
    "shopping-cart.js": "shopping-cart",
    "checkout-page.js": "checkout-page",
    "order-confirmation.js": "order-confirmation",
    "imprint-page.js": "imprint-page",
    "terms-page.js": "terms-page",
    "contact-page.js": "contact-page",
    "not-found.js": "not-found",
}


def read_component(filename: str) -> str:
    return (COMPONENT_DIR / filename).read_text(encoding="utf-8")


def run_node_script(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["node", "--input-type=module", "--eval", script],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )


def test_all_architected_web_components_are_registered() -> None:
    app_source = read_component("app.js")

    for filename, tag_name in EXPECTED_COMPONENTS.items():
        source = read_component(filename)

        assert f'import "./{filename}";' in app_source
        assert "extends HTMLElement" in source
        assert f'customElements.define("{tag_name}"' in source


def test_index_bootstraps_tailwind_and_app_root() -> None:
    index = (PROJECT_ROOT / "frontend" / "index.html").read_text(encoding="utf-8")

    assert '<script src="https://cdn.tailwindcss.com"></script>' in index
    assert '<link rel="stylesheet" href="/styles/app.css" />' in index
    assert "<app-root></app-root>" in index
    assert '<script type="module" src="/components/app.js"></script>' in index


def test_app_router_maps_all_required_frontend_routes() -> None:
    source = read_component("app.js")

    expected_routes = {
        'route === "/"': "<product-list></product-list>",
        'route.startsWith("/products/")': "<product-detail></product-detail>",
        'route === "/cart"': "<shopping-cart></shopping-cart>",
        'route === "/checkout"': "<checkout-page></checkout-page>",
        'route.startsWith("/orders/")': "<order-confirmation></order-confirmation>",
        'route === "/imprint"': "<imprint-page></imprint-page>",
        'route === "/terms"': "<terms-page></terms-page>",
        'route === "/contact"': "<contact-page></contact-page>",
        "return \"<not-found></not-found>\"": "<not-found></not-found>",
    }

    for route_check, component_markup in expected_routes.items():
        assert route_check in source
        assert component_markup in source

    assert "detail.productId = id" in source
    assert "confirmation.orderId = id" in source


def test_product_components_use_required_api_contracts_and_ui_hooks() -> None:
    list_source = read_component("product-list.js")
    detail_source = read_component("product-detail.js")

    assert 'api.get("/api/products")' in list_source
    assert "data-search" in list_source
    assert "data-brand" in list_source
    assert 'href="#/products/${product.id}"' in list_source

    assert "api.get(`/api/products/${this._productId}`)" in detail_source
    assert "api.get(`/api/products/${this._productId}/reviews`)" in detail_source
    assert 'api.post("/api/cart/items"' in detail_source
    assert "product_id: this.product.id" in detail_source
    assert "quantity: Number(form.get(\"quantity\"))" in detail_source
    assert "api.post(`/api/products/${this.product.id}/reviews`" in detail_source
    assert 'new CustomEvent("cart:changed")' in detail_source
    assert 'static get observedAttributes()' in detail_source
    assert 'return ["product-id"];' in detail_source
    assert "connectedCallback()" in detail_source
    assert "attributeChangedCallback" in detail_source


def test_cart_checkout_and_order_components_use_required_api_contracts() -> None:
    cart_source = read_component("shopping-cart.js")
    checkout_source = read_component("checkout-page.js")
    confirmation_source = read_component("order-confirmation.js")

    assert 'api.get("/api/cart")' in cart_source
    assert "api.patch(`/api/cart/items/${itemId}`" in cart_source
    assert "api.delete(`/api/cart/items/${event.currentTarget.dataset.remove}`)" in cart_source
    assert 'setRoute("/checkout")' in cart_source

    assert 'api.get("/api/cart")' in checkout_source
    assert 'api.post("/api/orders"' in checkout_source
    assert "shipping:" in checkout_source
    assert 'payment_method: form.get("payment_method")' in checkout_source
    assert "setRoute(`/orders/${order.order_id}`)" in checkout_source

    assert "api.get(`/api/orders/${this._orderId}`)" in confirmation_source
    assert "this.order.items.map" in confirmation_source
    assert "shipping_name" in confirmation_source
    assert 'return ["order-id"];' in confirmation_source


def test_checkout_and_contact_components_define_expected_form_behaviour() -> None:
    checkout_source = read_component("checkout-page.js")
    contact_source = read_component("contact-page.js")

    for field in ("name", "email", "street", "zip", "city", "country"):
        assert f'this.input("{field}"' in checkout_source

    assert 'this.input("email", "E-Mail", "email")' in checkout_source
    assert "required" in checkout_source
    assert "event.preventDefault();" in checkout_source
    assert 'window.dispatchEvent(new CustomEvent("cart:changed"))' in checkout_source

    assert "data-contact-form" in contact_source
    assert 'name="name"' in contact_source
    assert 'name="email"' in contact_source
    assert 'name="message"' in contact_source
    assert "event.preventDefault();" in contact_source
    assert "event.currentTarget.reset();" in contact_source
    assert "Nachricht wurde erfasst." in contact_source


def test_static_page_components_render_required_content() -> None:
    imprint_source = read_component("imprint-page.js")
    terms_source = read_component("terms-page.js")
    not_found_source = read_component("not-found.js")

    assert "Sole Market GmbH" in imprint_source
    assert "service@sole-market.example" in imprint_source
    assert "Allgemeine Geschaeftsbedingungen" in terms_source
    assert "Vertragsschluss" in terms_source
    assert "Die angeforderte Seite wurde nicht gefunden." in not_found_source
    assert "escapeHtml(message)" in not_found_source


def test_frontend_api_helpers_behave_correctly_in_node() -> None:
    script = textwrap.dedent(
        f"""
        globalThis.window = {{ location: {{ hash: "" }} }};
        const calls = [];
        globalThis.fetch = async (path, options = {{}}) => {{
          calls.push({{ path, options }});
          if (path === "/fail") {{
            return {{
              ok: false,
              status: 400,
              async json() {{ return {{ detail: "Bad request" }}; }},
            }};
          }}
          if (options.method === "PATCH") {{
            return {{ ok: true, status: 204, async json() {{ return {{}}; }} }};
          }}
          return {{
            ok: true,
            status: 200,
            async json() {{ return {{ ok: true, path }}; }},
          }};
        }};

        const module = await import({(COMPONENT_DIR / "api.js").as_uri()!r});

        if (module.escapeHtml("<script>'&\\"</script>") !== "&lt;script&gt;&#039;&amp;&quot;&lt;/script&gt;") {{
          throw new Error("escapeHtml did not encode unsafe characters");
        }}

        const price = module.formatMoney(129.95, "EUR");
        if (!price.includes("129,95") || !/\\p{{Sc}}/u.test(price)) {{
          throw new Error(`formatMoney returned unexpected value: ${{price}}`);
        }}

        const placeholder = module.placeholderImage("Runner");
        if (!placeholder.startsWith("data:image/svg+xml;charset=UTF-8,")) {{
          throw new Error("placeholderImage did not return an SVG data URL");
        }}

        module.setRoute("/cart");
        if (globalThis.window.location.hash !== "/cart" || module.currentRoute() !== "/cart") {{
          throw new Error("route helpers did not update or read window.location.hash");
        }}

        const result = await module.api.post("/ok", {{ quantity: 2 }});
        if (!result.ok || calls.at(-1).options.method !== "POST") {{
          throw new Error("api.post did not issue a POST request");
        }}
        if (calls.at(-1).options.headers["Content-Type"] !== "application/json") {{
          throw new Error("api.post did not set JSON headers");
        }}
        if (calls.at(-1).options.body !== JSON.stringify({{ quantity: 2 }})) {{
          throw new Error("api.post did not serialize payload");
        }}

        const empty = await module.api.patch("/ok", {{ quantity: 1 }});
        if (empty !== null) {{
          throw new Error("api.patch did not return null for 204 responses");
        }}

        try {{
          await module.api.get("/fail");
          throw new Error("api.get did not throw for failed responses");
        }} catch (error) {{
          if (error.message !== "Bad request") {{
            throw error;
          }}
        }}
        """
    )

    result = run_node_script(script)

    assert result.returncode == 0, result.stderr


def test_detail_and_order_components_support_attribute_driven_loading() -> None:
    detail_source = read_component("product-detail.js")
    confirmation_source = read_component("order-confirmation.js")

    assert 'const productId = Number(this.getAttribute("product-id"));' in detail_source
    assert "this.productId = productId;" in detail_source
    assert 'name === "product-id"' in detail_source
    assert "this.productId = Number(newValue);" in detail_source
    assert "if (!this._productId)" in detail_source

    assert 'const orderId = Number(this.getAttribute("order-id"));' in confirmation_source
    assert "this.orderId = orderId;" in confirmation_source
    assert 'name === "order-id"' in confirmation_source
    assert "this.orderId = Number(newValue);" in confirmation_source
    assert "if (!this._orderId)" in confirmation_source


def test_web_component_modules_import_in_node_smoke_environment() -> None:
    script = textwrap.dedent(
        f"""
        globalThis.window = {{
          location: {{ hash: "" }},
          addEventListener() {{}},
          dispatchEvent() {{}},
        }};
        globalThis.CustomEvent = class CustomEvent {{
          constructor(type) {{
            this.type = type;
          }}
        }};
        globalThis.HTMLElement = class HTMLElement {{
          constructor() {{
            this.innerHTML = "";
          }}
        }};
        const registry = new Map();
        globalThis.customElements = {{
          define(name, klass) {{
            registry.set(name, klass);
          }},
          get(name) {{
            return registry.get(name);
          }},
        }};

        await import({(COMPONENT_DIR / "app.js").as_uri()!r});

        const expected = {sorted(EXPECTED_COMPONENTS.values())!r};
        expected.push("app-root");
        const missing = expected.filter((name) => !registry.has(name));
        if (missing.length) {{
          throw new Error(`Missing custom elements: ${{missing.join(", ")}}`);
        }}
        """
    )

    result = run_node_script(script)

    assert result.returncode == 0, result.stderr


def test_web_component_render_methods_behave_in_node_smoke_environment() -> None:
    script = textwrap.dedent(
        f"""
        globalThis.window = {{
          location: {{ hash: "" }},
          addEventListener() {{}},
          dispatchEvent() {{}},
        }};
        globalThis.CustomEvent = class CustomEvent {{
          constructor(type) {{
            this.type = type;
          }}
        }};
        globalThis.HTMLElement = class HTMLElement {{
          constructor() {{
            this.innerHTML = "";
            this.isConnected = true;
            this.attrs = new Map();
            this.nodes = new Map();
          }}
          getAttribute(name) {{
            return this.attrs.get(name) || null;
          }}
          setAttribute(name, value) {{
            this.attrs.set(name, String(value));
          }}
          querySelector(selector) {{
            if (!this.nodes.has(selector)) {{
              this.nodes.set(selector, {{
                className: "",
                dataset: {{}},
                listeners: {{}},
                textContent: "",
                value: "",
                addEventListener(type, callback) {{
                  this.listeners[type] = callback;
                }},
                reset() {{
                  this.wasReset = true;
                }},
              }});
            }}
            return this.nodes.get(selector);
          }}
          querySelectorAll() {{
            return [];
          }}
        }};
        const registry = new Map();
        globalThis.customElements = {{
          define(name, klass) {{
            registry.set(name, klass);
          }},
          get(name) {{
            return registry.get(name);
          }},
        }};

        await import({(COMPONENT_DIR / "product-list.js").as_uri()!r});
        await import({(COMPONENT_DIR / "shopping-cart.js").as_uri()!r});
        await import({(COMPONENT_DIR / "checkout-page.js").as_uri()!r});
        await import({(COMPONENT_DIR / "order-confirmation.js").as_uri()!r});
        await import({(COMPONENT_DIR / "imprint-page.js").as_uri()!r});
        await import({(COMPONENT_DIR / "terms-page.js").as_uri()!r});
        await import({(COMPONENT_DIR / "contact-page.js").as_uri()!r});
        await import({(COMPONENT_DIR / "not-found.js").as_uri()!r});

        const ProductList = registry.get("product-list");
        const productList = new ProductList();
        const card = productList.productCard({{
          id: 7,
          name: "Runner <Pro>",
          brand: "ACME",
          price: 129.95,
          currency: "EUR",
          short_description: "Leicht und schnell",
          image_url: "/images/runner.jpg",
          rating: 4.6,
          is_new: true,
        }});
        if (!card.includes('href="#/products/7"') || !card.includes("Runner &lt;Pro&gt;")) {{
          throw new Error("product card did not render escaped detail link");
        }}
        if (!card.includes("Neu") || !card.includes("4.6 / 5")) {{
          throw new Error("product card did not render product badges and rating");
        }}

        const ShoppingCart = registry.get("shopping-cart");
        const shoppingCart = new ShoppingCart();
        const cartItem = shoppingCart.renderItem({{
          item_id: 3,
          image_url: "/images/cart.jpg",
          name: "Daily Runner",
          brand: "ACME",
          size: "42",
          quantity: 2,
          line_total: 259.9,
          currency: "EUR",
        }});
        if (!cartItem.includes('data-quantity="3"') || !cartItem.includes('data-remove="3"')) {{
          throw new Error("cart item did not expose quantity and remove controls");
        }}
        if (!cartItem.includes("Groesse 42") || !cartItem.includes("Entfernen")) {{
          throw new Error("cart item did not render size and remove action");
        }}

        const CheckoutPage = registry.get("checkout-page");
        const checkoutPage = new CheckoutPage();
        const emailInput = checkoutPage.input("email", "E-Mail", "email");
        if (!emailInput.includes('name="email"') || !emailInput.includes('type="email"') || !emailInput.includes("required")) {{
          throw new Error("checkout input helper did not render required field metadata");
        }}

        const OrderConfirmation = registry.get("order-confirmation");
        const orderConfirmation = new OrderConfirmation();
        const orderItem = orderConfirmation.renderItem({{
          image_url_snapshot: "/images/order.jpg",
          name_snapshot: "Court Classic",
          brand_snapshot: "Sole",
          size: "43",
          quantity: 1,
          line_total: 89.99,
        }});
        if (!orderItem.includes("Court Classic") || !orderItem.includes("Groesse 43")) {{
          throw new Error("order item did not render snapshot data");
        }}

        for (const name of ["imprint-page", "terms-page"]) {{
          const Component = registry.get(name);
          const element = new Component();
          element.connectedCallback();
          if (!element.innerHTML.includes("<section") || !element.innerHTML.includes("Sole Market")) {{
            throw new Error(`${{name}} did not render static page content`);
          }}
        }}

        const NotFound = registry.get("not-found");
        const notFound = new NotFound();
        notFound.setAttribute("message", "<missing>");
        notFound.connectedCallback();
        if (!notFound.innerHTML.includes("&lt;missing&gt;")) {{
          throw new Error("not-found did not escape custom messages");
        }}

        const ContactPage = registry.get("contact-page");
        const contactPage = new ContactPage();
        contactPage.connectedCallback();
        if (!contactPage.innerHTML.includes('name="name"') || !contactPage.innerHTML.includes('name="message"')) {{
          throw new Error("contact form did not render named fields");
        }}
        const form = contactPage.querySelector("[data-contact-form]");
        const status = contactPage.querySelector("[data-status]");
        let prevented = false;
        const submittedForm = {{
          reset() {{
            this.wasReset = true;
          }},
        }};
        form.listeners.submit({{
          preventDefault() {{
            prevented = true;
          }},
          currentTarget: submittedForm,
        }});
        if (!prevented || !submittedForm.wasReset || status.textContent !== "Nachricht wurde erfasst.") {{
          throw new Error("contact form submit handler did not prevent, reset, and report success");
        }}
        """
    )

    result = run_node_script(script)

    assert result.returncode == 0, result.stderr


def test_app_root_resolves_routes_and_updates_cart_badge_in_node() -> None:
    script = textwrap.dedent(
        f"""
        globalThis.window = {{
          location: {{ hash: "" }},
          addEventListener() {{}},
          dispatchEvent() {{}},
        }};
        globalThis.fetch = async (path) => {{
          if (path !== "/api/cart") {{
            throw new Error(`Unexpected fetch path: ${{path}}`);
          }}
          return {{
            ok: true,
            status: 200,
            async json() {{
              return {{
                items: [
                  {{ quantity: 2 }},
                  {{ quantity: 3 }},
                ],
              }};
            }},
          }};
        }};
        globalThis.CustomEvent = class CustomEvent {{
          constructor(type) {{
            this.type = type;
          }}
        }};
        globalThis.HTMLElement = class HTMLElement {{
          constructor() {{
            this.innerHTML = "";
            this.nodes = new Map();
          }}
          querySelector(selector) {{
            if (!this.nodes.has(selector)) {{
              this.nodes.set(selector, {{ textContent: "" }});
            }}
            return this.nodes.get(selector);
          }}
        }};
        const registry = new Map();
        globalThis.customElements = {{
          define(name, klass) {{
            registry.set(name, klass);
          }},
          get(name) {{
            return registry.get(name);
          }},
        }};

        await import({(COMPONENT_DIR / "app.js").as_uri()!r});

        const AppRoot = registry.get("app-root");
        const app = new AppRoot();

        const expectations = new Map([
          ["/", "<product-list></product-list>"],
          ["/products/4", "<product-detail></product-detail>"],
          ["/products/not-a-number", "<not-found></not-found>"],
          ["/cart", "<shopping-cart></shopping-cart>"],
          ["/checkout", "<checkout-page></checkout-page>"],
          ["/orders/9", "<order-confirmation></order-confirmation>"],
          ["/orders/new", "<not-found></not-found>"],
          ["/imprint", "<imprint-page></imprint-page>"],
          ["/terms", "<terms-page></terms-page>"],
          ["/contact", "<contact-page></contact-page>"],
          ["/missing", "<not-found></not-found>"],
        ]);

        for (const [route, markup] of expectations.entries()) {{
          if (app.resolvePage(route) !== markup) {{
            throw new Error(`Unexpected component for ${{route}}`);
          }}
        }}

        await app.loadCartCount();
        if (app.cartCount !== 5) {{
          throw new Error(`Unexpected cart count: ${{app.cartCount}}`);
        }}
        if (app.querySelector("[data-cart-count]").textContent !== "5") {{
          throw new Error("Cart badge was not updated");
        }}
        """
    )

    result = run_node_script(script)

    assert result.returncode == 0, result.stderr


def test_product_detail_submit_handlers_call_cart_and_review_apis() -> None:
    script = textwrap.dedent(
        f"""
        const requests = [];
        const dispatched = [];

        globalThis.window = {{
          location: {{ hash: "" }},
          addEventListener() {{}},
          dispatchEvent(event) {{
            dispatched.push(event.type);
          }},
        }};
        globalThis.setTimeout = (callback) => callback();
        globalThis.CustomEvent = class CustomEvent {{
          constructor(type) {{
            this.type = type;
          }}
        }};
        globalThis.fetch = async (path, options = {{}}) => {{
          requests.push({{ path, options }});
          return {{
            ok: true,
            status: 201,
            async json() {{
              return {{ ok: true }};
            }},
          }};
        }};
        globalThis.FormData = class FormData {{
          constructor(form) {{
            this.values = form.values;
          }}
          get(name) {{
            return this.values[name] ?? null;
          }}
        }};
        globalThis.HTMLElement = class HTMLElement {{
          constructor() {{
            this.innerHTML = "";
            this.nodes = new Map();
          }}
          querySelector(selector) {{
            if (!this.nodes.has(selector)) {{
              this.nodes.set(selector, {{
                className: "",
                listeners: {{}},
                textContent: "",
                addEventListener(type, callback) {{
                  this.listeners[type] = callback;
                }},
              }});
            }}
            return this.nodes.get(selector);
          }}
        }};
        const registry = new Map();
        globalThis.customElements = {{
          define(name, klass) {{
            registry.set(name, klass);
          }},
          get(name) {{
            return registry.get(name);
          }},
        }};

        await import({(COMPONENT_DIR / "product-detail.js").as_uri()!r});

        const ProductDetail = registry.get("product-detail");
        const detail = new ProductDetail();
        detail.product = {{
          id: 11,
          name: "Tempo",
          brand: "Sole",
          price: 99.95,
          currency: "EUR",
          long_description: "Leichter Sneaker",
          image_url: "/tempo.jpg",
          sizes: ["41", "42"],
          color: "Weiss",
          material: "Mesh",
          stock: 8,
          rating: 4.4,
        }};
        detail.reviewData = {{ reviews: [] }};
        detail.load = async () => {{
          detail.reviewReloaded = true;
        }};
        detail.render();

        const cartForm = detail.querySelector("[data-cart-form]");
        cartForm.values = {{ size: "42", quantity: "2" }};
        await cartForm.listeners.submit({{
          preventDefault() {{}},
          currentTarget: cartForm,
        }});

        const cartRequest = requests.at(-1);
        if (cartRequest.path !== "/api/cart/items") {{
          throw new Error(`Unexpected cart request path: ${{cartRequest.path}}`);
        }}
        if (cartRequest.options.method !== "POST") {{
          throw new Error("Cart handler did not use POST");
        }}
        const cartPayload = JSON.parse(cartRequest.options.body);
        if (cartPayload.product_id !== 11 || cartPayload.size !== "42" || cartPayload.quantity !== 2) {{
          throw new Error(`Unexpected cart payload: ${{cartRequest.options.body}}`);
        }}
        if (!dispatched.includes("cart:changed")) {{
          throw new Error("Cart handler did not dispatch cart:changed");
        }}
        if (globalThis.window.location.hash !== "/cart") {{
          throw new Error("Cart handler did not navigate to cart");
        }}

        const reviewForm = detail.querySelector("[data-review-form]");
        reviewForm.values = {{
          author: "Ada",
          rating: "5",
          comment: "Sehr bequem",
        }};
        await reviewForm.listeners.submit({{
          preventDefault() {{}},
          currentTarget: reviewForm,
        }});

        const reviewRequest = requests.at(-1);
        if (reviewRequest.path !== "/api/products/11/reviews") {{
          throw new Error(`Unexpected review request path: ${{reviewRequest.path}}`);
        }}
        const reviewPayload = JSON.parse(reviewRequest.options.body);
        if (reviewPayload.author !== "Ada" || reviewPayload.rating !== 5 || reviewPayload.comment !== "Sehr bequem") {{
          throw new Error(`Unexpected review payload: ${{reviewRequest.options.body}}`);
        }}
        if (!detail.reviewReloaded) {{
          throw new Error("Review handler did not reload product detail");
        }}
        """
    )

    result = run_node_script(script)

    assert result.returncode == 0, result.stderr
