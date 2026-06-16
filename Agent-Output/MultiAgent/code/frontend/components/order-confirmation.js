import { api, escapeHtml, formatMoney, placeholderImage } from "./api.js";

class OrderConfirmation extends HTMLElement {
  static get observedAttributes() {
    return ["order-id"];
  }

  connectedCallback() {
    const orderId = Number(this.getAttribute("order-id"));
    if (orderId && orderId !== this._orderId) {
      this.orderId = orderId;
    }
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (name === "order-id" && oldValue !== newValue && this.isConnected) {
      this.orderId = Number(newValue);
    }
  }

  set orderId(value) {
    this._orderId = value;
    this.load();
  }

  async load() {
    if (!this._orderId) {
      return;
    }
    this.innerHTML = "<p class='text-zinc-600'>Bestellung wird geladen...</p>";
    try {
      this.order = await api.get(`/api/orders/${this._orderId}`);
      this.render();
    } catch (error) {
      this.innerHTML = `<not-found message="${escapeHtml(error.message)}"></not-found>`;
    }
  }

  render() {
    this.innerHTML = `
      <section class="rounded-lg border border-zinc-200 bg-white p-6">
        <p class="mb-2 text-sm font-semibold uppercase tracking-normal text-teal-700">Bestellung eingegangen</p>
        <h1 class="text-2xl font-bold sm:text-3xl">Danke fuer deine Bestellung #${this.order.id}</h1>
        <p class="mt-2 text-zinc-600">Status: ${escapeHtml(this.order.status)}</p>
        <div class="mt-6 grid gap-6 lg:grid-cols-2">
          <div>
            <h2 class="mb-3 text-xl font-bold">Lieferadresse</h2>
            <p>${escapeHtml(this.order.shipping_name)}</p>
            <p>${escapeHtml(this.order.shipping_street)}</p>
            <p>${escapeHtml(this.order.shipping_zip)} ${escapeHtml(this.order.shipping_city)}</p>
            <p>${escapeHtml(this.order.shipping_country)}</p>
            <p class="mt-2 text-zinc-600">${escapeHtml(this.order.email)}</p>
          </div>
          <div>
            <h2 class="mb-3 text-xl font-bold">Positionen</h2>
            <div class="space-y-3">
              ${this.order.items.map((item) => this.renderItem(item)).join("")}
            </div>
            <div class="mt-5 flex justify-between border-t border-zinc-200 pt-4 text-lg font-bold">
              <span>Gesamt</span><span>${formatMoney(this.order.total, "EUR")}</span>
            </div>
          </div>
        </div>
      </section>
    `;
  }

  renderItem(item) {
    return `
      <article class="grid gap-3 text-sm sm:grid-cols-[72px_1fr_auto]">
        <img class="h-16 w-16 rounded-md bg-zinc-100 object-cover" src="${escapeHtml(item.image_url_snapshot)}" alt="${escapeHtml(item.name_snapshot)}" onerror="this.src='${placeholderImage(item.name_snapshot)}'" />
        <div class="min-w-0">
          <strong>${escapeHtml(item.name_snapshot)}</strong>
          <p class="text-zinc-600">${escapeHtml(item.brand_snapshot)}, Groesse ${escapeHtml(item.size)}, ${item.quantity}x</p>
        </div>
        <span class="font-semibold sm:text-right">${formatMoney(item.line_total, "EUR")}</span>
      </article>
    `;
  }
}

customElements.define("order-confirmation", OrderConfirmation);
