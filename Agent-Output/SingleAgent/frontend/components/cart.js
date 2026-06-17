import { formatMoney, friendlyError, refreshCartBadge, shopFetch, skeletonCards } from "./api.js";

class ShoppingCart extends HTMLElement {
  connectedCallback() {
    this.innerHTML = skeletonCards(2);
    this.load();
  }

  async load() {
    try {
      this.cart = await shopFetch("/api/cart");
      this.render();
      refreshCartBadge();
    } catch (error) {
      this.innerHTML = friendlyError(error.message);
    }
  }

  render() {
    if (!this.cart.items.length) {
      this.innerHTML = `
        <section class="rounded-[2rem] bg-white p-10 text-center shadow-xl ring-1 ring-stone-200">
          <h1 class="font-display text-4xl font-bold">Dein Warenkorb ist leer.</h1>
          <p class="mt-3 text-stone-600">Finde dein naechstes Lieblingspaar bei SneakerHaus.</p>
          <a class="focus-ring mt-6 inline-flex rounded-full bg-ink px-6 py-3 font-bold text-white hover:bg-clay" href="/#/">Weiter shoppen</a>
        </section>
      `;
      return;
    }
    this.innerHTML = `
      <section class="grid gap-8 lg:grid-cols-[1fr_380px]">
        <div>
          <h1 class="font-display text-4xl font-bold">Warenkorb</h1>
          <div class="mt-6 space-y-4">
            ${this.cart.items.map((item) => `
              <article class="grid gap-4 rounded-3xl bg-white p-4 shadow-sm ring-1 ring-stone-200 sm:grid-cols-[120px_1fr]">
                <img class="h-32 w-full rounded-2xl object-cover sm:h-full" src="${item.image_url}" alt="${item.name}" />
                <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p class="text-sm font-bold text-clay">${item.brand}</p>
                    <h2 class="font-display text-2xl font-bold">${item.name}</h2>
                    <p class="mt-1 text-sm text-stone-600">Groesse ${item.size} · Einzelpreis ${formatMoney(item.price, item.currency)}</p>
                    <button data-remove="${item.id}" class="focus-ring mt-3 rounded-full border border-stone-200 px-4 py-2 text-sm font-bold hover:bg-stone-100">Entfernen</button>
                  </div>
                  <div class="text-right">
                    <div class="mb-3 inline-flex items-center rounded-full border border-stone-200 bg-white">
                      <button data-dec="${item.id}" class="focus-ring px-4 py-3 font-bold">−</button>
                      <span class="min-w-10 text-center font-bold">${item.quantity}</span>
                      <button data-inc="${item.id}" class="focus-ring px-4 py-3 font-bold">+</button>
                    </div>
                    <p class="font-display text-2xl font-bold">${formatMoney(item.line_total, item.currency)}</p>
                  </div>
                </div>
              </article>
            `).join("")}
          </div>
        </div>
        <aside class="h-fit rounded-[2rem] bg-ink p-6 text-white shadow-xl">
          <h2 class="font-display text-3xl font-bold">Summe</h2>
          <div class="mt-6 space-y-3 text-sm">
            <div class="flex justify-between"><span>Zwischensumme</span><strong>${formatMoney(this.cart.subtotal)}</strong></div>
            <div class="flex justify-between"><span>Versand</span><strong>0,00 €</strong></div>
            <div class="border-t border-white/20 pt-3 flex justify-between text-lg"><span>Gesamt</span><strong>${formatMoney(this.cart.total)}</strong></div>
          </div>
          <a class="focus-ring mt-6 inline-flex w-full justify-center rounded-full bg-clay px-6 py-3 font-bold text-white hover:bg-[#9f4d2e]" href="/#/checkout">Zur Kasse</a>
        </aside>
      </section>
    `;
    this.bindEvents();
  }

  bindEvents() {
    this.querySelectorAll("[data-remove]").forEach((button) => button.addEventListener("click", async () => {
      await shopFetch(`/api/cart/items/${button.dataset.remove}`, { method: "DELETE" });
      this.load();
    }));
    this.querySelectorAll("[data-dec], [data-inc]").forEach((button) => button.addEventListener("click", async () => {
      const id = button.dataset.dec || button.dataset.inc;
      const item = this.cart.items.find((entry) => entry.id === Number(id));
      const quantity = Math.max(1, item.quantity + (button.dataset.inc ? 1 : -1));
      await shopFetch(`/api/cart/items/${id}`, { method: "PATCH", body: JSON.stringify({ quantity }) });
      this.load();
    }));
  }
}

customElements.define("shopping-cart", ShoppingCart);
