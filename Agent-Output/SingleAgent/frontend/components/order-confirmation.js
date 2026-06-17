import { formatMoney, friendlyError, shopFetch, skeletonCards } from "./api.js";

class OrderConfirmation extends HTMLElement {
  connectedCallback() {
    this.orderId = this.getAttribute("order-id");
    this.innerHTML = skeletonCards(1);
    this.load();
  }

  async load() {
    try {
      this.order = await shopFetch(`/api/orders/${this.orderId}`);
      this.render();
    } catch (error) {
      this.innerHTML = friendlyError(error.message);
    }
  }

  render() {
    const order = this.order;
    const payment = order.payment_method === "invoice" ? "Auf Rechnung" : "Kreditkarte (Demo)";
    this.innerHTML = `
      <section class="rounded-[2rem] bg-white p-6 shadow-xl ring-1 ring-stone-200 md:p-10">
        <p class="inline-flex rounded-full bg-green-50 px-4 py-2 text-sm font-bold text-green-800">Bestellung bestaetigt</p>
        <h1 class="mt-5 font-display text-4xl font-bold">Vielen Dank fuer deine Bestellung bei SneakerHaus!</h1>
        <p class="mt-3 text-stone-600">Wir haben deine Bestellung erhalten und bereiten sie fuer den Versand vor.</p>
        <div class="mt-8 grid gap-4 md:grid-cols-3">
          <div class="rounded-3xl bg-sand p-5"><p class="text-sm font-bold text-stone-600">Bestellnummer</p><p class="font-display text-2xl font-bold">#${order.order_id}</p></div>
          <div class="rounded-3xl bg-sand p-5"><p class="text-sm font-bold text-stone-600">Datum</p><p class="font-bold">${new Date(order.created_at).toLocaleString("de-DE")}</p></div>
          <div class="rounded-3xl bg-sand p-5"><p class="text-sm font-bold text-stone-600">Zahlung</p><p class="font-bold">${payment}</p></div>
        </div>
        <div class="mt-8 grid gap-8 lg:grid-cols-[1fr_0.8fr]">
          <div>
            <h2 class="font-display text-2xl font-bold">Positionen</h2>
            <div class="mt-4 space-y-4">
              ${order.items.map((item) => `
                <div class="flex gap-4 rounded-3xl border border-stone-200 p-4">
                  <img class="h-20 w-20 rounded-2xl object-cover" src="${item.image_url}" alt="${item.name}" />
                  <div class="flex-1">
                    <p class="font-bold">${item.name}</p>
                    <p class="text-sm text-stone-600">${item.brand} · Groesse ${item.size} · ${item.quantity}x</p>
                  </div>
                  <strong>${formatMoney(item.line_total)}</strong>
                </div>
              `).join("")}
            </div>
          </div>
          <div class="rounded-3xl bg-ink p-6 text-white">
            <h2 class="font-display text-2xl font-bold">Lieferadresse</h2>
            <p class="mt-4 text-stone-200">${order.shipping.name}<br>${order.shipping.street}<br>${order.shipping.zip} ${order.shipping.city}<br>${order.shipping.country}<br>${order.shipping.email}</p>
            <div class="mt-6 border-t border-white/20 pt-4 flex justify-between text-lg"><span>Gesamt</span><strong>${formatMoney(order.total)}</strong></div>
          </div>
        </div>
        <a class="focus-ring mt-8 inline-flex rounded-full bg-clay px-6 py-3 font-bold text-white hover:bg-[#9f4d2e]" href="/#/">Weiter shoppen</a>
      </section>
    `;
  }
}

customElements.define("order-confirmation", OrderConfirmation);
