import { api, escapeHtml, formatMoney, placeholderImage, setRoute } from "./api.js";

class ShoppingCart extends HTMLElement {
  connectedCallback() {
    this.load();
  }

  async load() {
    this.innerHTML = "<p class='text-zinc-600'>Warenkorb wird geladen...</p>";
    try {
      this.cart = await api.get("/api/cart");
      this.render();
    } catch (error) {
      this.innerHTML = `<p class="text-red-700">${error.message}</p>`;
    }
  }

  render() {
    if (!this.cart.items.length) {
      this.innerHTML = `
        <section class="rounded-lg border border-zinc-200 bg-white p-8 text-center">
          <h1 class="text-3xl font-bold">Der Warenkorb ist leer.</h1>
          <a class="mt-5 inline-flex rounded-md bg-zinc-950 px-4 py-3 font-bold text-white" href="#/">Produkte ansehen</a>
        </section>
      `;
      return;
    }

    this.innerHTML = `
      <section class="grid gap-8 lg:grid-cols-[1fr_360px]">
        <div>
          <h1 class="mb-5 text-3xl font-bold">Warenkorb</h1>
          <div class="space-y-3">
            ${this.cart.items.map((item) => this.renderItem(item)).join("")}
          </div>
        </div>
        <aside class="h-fit rounded-lg border border-zinc-200 bg-white p-5">
          <h2 class="mb-4 text-xl font-bold">Zusammenfassung</h2>
          <div class="mb-2 flex justify-between text-zinc-700"><span>Zwischensumme</span><span>${formatMoney(this.cart.subtotal, this.cart.currency)}</span></div>
          <div class="mb-5 flex justify-between text-lg font-bold"><span>Gesamt</span><span>${formatMoney(this.cart.total, this.cart.currency)}</span></div>
          <button data-checkout class="focus-ring w-full rounded-md bg-zinc-950 px-4 py-3 font-bold text-white hover:bg-zinc-800">Zur Kasse</button>
          <p data-status class="mt-3 text-sm"></p>
        </aside>
      </section>
    `;
    this.bindEvents();
  }

  renderItem(item) {
    return `
      <article class="grid gap-4 rounded-lg border border-zinc-200 bg-white p-4 sm:grid-cols-[120px_1fr_auto]">
        <img class="h-28 w-full rounded-md bg-zinc-100 object-cover sm:w-28" src="${escapeHtml(item.image_url)}" alt="${escapeHtml(item.name)}" onerror="this.src='${placeholderImage(item.name)}'" />
        <div>
          <p class="text-sm font-semibold text-zinc-500">${escapeHtml(item.brand)}</p>
          <h2 class="font-bold">${escapeHtml(item.name)}</h2>
          <p class="text-sm text-zinc-600">Groesse ${escapeHtml(item.size)}</p>
          <p class="mt-2 font-semibold">${formatMoney(item.line_total, item.currency)}</p>
        </div>
        <div class="flex items-center gap-2 sm:flex-col sm:items-end">
          <input data-quantity="${item.item_id}" class="focus-ring w-20 rounded-md border border-zinc-300 px-2 py-1" type="number" min="1" value="${item.quantity}" />
          <button data-remove="${item.item_id}" class="focus-ring rounded-md px-3 py-2 text-sm font-semibold text-red-700 hover:bg-red-50">Entfernen</button>
        </div>
      </article>
    `;
  }

  bindEvents() {
    this.querySelector("[data-checkout]").addEventListener("click", () => setRoute("/checkout"));
    const status = this.querySelector("[data-status]");
    this.querySelectorAll("[data-quantity]").forEach((input) => {
      input.addEventListener("change", async (event) => {
        const itemId = event.currentTarget.dataset.quantity;
        try {
          await api.patch(`/api/cart/items/${itemId}`, {
            quantity: Number(event.currentTarget.value),
          });
          window.dispatchEvent(new CustomEvent("cart:changed"));
          this.load();
        } catch (error) {
          status.className = "mt-3 text-sm text-red-700";
          status.textContent = error.message;
        }
      });
    });
    this.querySelectorAll("[data-remove]").forEach((button) => {
      button.addEventListener("click", async (event) => {
        try {
          await api.delete(`/api/cart/items/${event.currentTarget.dataset.remove}`);
          window.dispatchEvent(new CustomEvent("cart:changed"));
          this.load();
        } catch (error) {
          status.className = "mt-3 text-sm text-red-700";
          status.textContent = error.message;
        }
      });
    });
  }
}

customElements.define("shopping-cart", ShoppingCart);
