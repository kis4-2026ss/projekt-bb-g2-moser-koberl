import "./product-list.js";
import "./product-detail.js";
import "./shopping-cart.js";
import "./checkout-page.js";
import "./order-confirmation.js";
import "./imprint-page.js";
import "./terms-page.js";
import "./contact-page.js";
import "./not-found.js";
import { api, currentRoute, formatMoney, setRoute } from "./api.js";

class AppRoot extends HTMLElement {
  connectedCallback() {
    window.addEventListener("hashchange", () => this.render());
    window.addEventListener("cart:changed", () => this.loadCartCount());
    this.cartCount = 0;
    this.render();
    this.loadCartCount();
  }

  async loadCartCount() {
    try {
      const cart = await api.get("/api/cart");
      this.cartCount = cart.items.reduce((sum, item) => sum + item.quantity, 0);
      this.updateCartBadge();
    } catch {
      this.cartCount = 0;
      this.updateCartBadge();
    }
  }

  updateCartBadge() {
    const badge = this.querySelector("[data-cart-count]");
    if (badge) {
      badge.textContent = String(this.cartCount || 0);
    }
  }

  render() {
    const route = currentRoute();
    const page = this.resolvePage(route);
    this.innerHTML = `
      <header class="sticky top-0 z-20 border-b border-zinc-200 bg-white/95 backdrop-blur">
        <nav class="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
          <a class="text-xl font-bold tracking-normal" href="#/">Sole Market</a>
          <div class="grid grid-cols-3 gap-2 text-center text-sm font-medium sm:flex sm:items-center">
            <a class="rounded-md px-3 py-2 hover:bg-zinc-100 focus-ring" href="#/">Shop</a>
            <a class="rounded-md px-3 py-2 hover:bg-zinc-100 focus-ring" href="#/contact">Kontakt</a>
            <a class="rounded-md bg-zinc-950 px-3 py-2 text-white hover:bg-zinc-800 focus-ring" href="#/cart">
              Warenkorb <span data-cart-count class="ml-1 rounded bg-white px-1.5 py-0.5 text-xs text-zinc-950">0</span>
            </a>
          </div>
        </nav>
      </header>
      <main class="mx-auto max-w-6xl px-4 py-6 sm:py-8">${page}</main>
      <footer class="border-t border-zinc-200 bg-white">
        <div class="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-6 text-sm text-zinc-600">
          <span>Sole Market</span>
          <div class="flex gap-4">
            <a class="hover:text-zinc-950" href="#/imprint">Impressum</a>
            <a class="hover:text-zinc-950" href="#/terms">AGB</a>
            <a class="hover:text-zinc-950" href="#/contact">Kontakt</a>
          </div>
        </div>
      </footer>
    `;
    this.updateCartBadge();
    this.bindPage(route);
  }

  resolvePage(route) {
    if (route === "/") return "<product-list></product-list>";
    if (route.startsWith("/products/")) {
      return this.routeId(route, "products") ? "<product-detail></product-detail>" : "<not-found></not-found>";
    }
    if (route === "/cart") return "<shopping-cart></shopping-cart>";
    if (route === "/checkout") return "<checkout-page></checkout-page>";
    if (route.startsWith("/orders/")) {
      return this.routeId(route, "orders") ? "<order-confirmation></order-confirmation>" : "<not-found></not-found>";
    }
    if (route === "/imprint") return "<imprint-page></imprint-page>";
    if (route === "/terms") return "<terms-page></terms-page>";
    if (route === "/contact") return "<contact-page></contact-page>";
    return "<not-found></not-found>";
  }

  bindPage(route) {
    if (route.startsWith("/products/")) {
      const id = this.routeId(route, "products");
      const detail = this.querySelector("product-detail");
      if (id && detail) {
        detail.productId = id;
      }
    }
    if (route.startsWith("/orders/")) {
      const id = this.routeId(route, "orders");
      const confirmation = this.querySelector("order-confirmation");
      if (id && confirmation) {
        confirmation.orderId = id;
      }
    }
  }

  routeId(route, segment) {
    const match = route.match(new RegExp(`^/${segment}/(\\d+)$`));
    return match ? Number(match[1]) : null;
  }
}

customElements.define("app-root", AppRoot);

export { api, formatMoney, setRoute };
