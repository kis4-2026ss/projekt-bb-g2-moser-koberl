import { refreshCartBadge } from "./api.js";

class SiteHeader extends HTMLElement {
  connectedCallback() {
    this.render(0);
    window.addEventListener("cart-updated", (event) => this.render(event.detail?.item_count || 0));
    refreshCartBadge();
  }

  render(count) {
    this.innerHTML = `
      <header class="sticky top-0 z-40 border-b border-stone-200/80 bg-sand/85 backdrop-blur-xl">
        <div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <a href="/#/" class="focus-ring rounded-xl font-display text-2xl font-bold tracking-tight text-ink">SneakerHaus</a>
          <nav class="flex items-center gap-2 text-sm font-bold">
            <a class="focus-ring rounded-full px-4 py-2 transition hover:bg-white" href="/#/">Shop</a>
            <a class="focus-ring relative rounded-full bg-ink px-4 py-2 text-white shadow-lg transition hover:-translate-y-0.5 hover:bg-clay" href="/#/cart">
              Warenkorb
              <span class="ml-2 inline-flex min-w-6 items-center justify-center rounded-full bg-clay px-2 py-0.5 text-xs text-white">${count}</span>
            </a>
          </nav>
        </div>
      </header>
    `;
  }
}

class SiteFooter extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <footer class="mt-16 border-t border-stone-200 bg-ink text-white">
        <div class="mx-auto grid max-w-7xl gap-8 px-4 py-10 sm:grid-cols-3 sm:px-6 lg:px-8">
          <div>
            <p class="font-display text-xl font-bold">SneakerHaus</p>
            <p class="mt-2 text-sm text-stone-300">SneakerHaus - Sneaker, die bewegen.</p>
          </div>
          <div class="grid gap-2 text-sm">
            <a class="w-fit rounded-lg text-stone-200 hover:text-white focus-ring" href="/#/legal/imprint">Impressum</a>
            <a class="w-fit rounded-lg text-stone-200 hover:text-white focus-ring" href="/#/legal/terms">AGB & Widerruf</a>
            <a class="w-fit rounded-lg text-stone-200 hover:text-white focus-ring" href="/#/legal/contact">Kontakt</a>
          </div>
          <div class="text-sm text-stone-300 sm:text-right">© ${new Date().getFullYear()} SneakerHaus. Alle Rechte vorbehalten.</div>
        </div>
      </footer>
    `;
  }
}

customElements.define("site-header", SiteHeader);
customElements.define("site-footer", SiteFooter);
