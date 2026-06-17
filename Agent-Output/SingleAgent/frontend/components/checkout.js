import { formatMoney, friendlyError, refreshCartBadge, shopFetch, skeletonCards } from "./api.js";

class CheckoutPage extends HTMLElement {
  connectedCallback() {
    this.innerHTML = skeletonCards(1);
    this.load();
  }

  async load() {
    try {
      this.cart = await shopFetch("/api/cart");
      this.render();
    } catch (error) {
      this.innerHTML = friendlyError(error.message);
    }
  }

  render() {
    if (!this.cart.items.length) {
      this.innerHTML = `
        <section class="rounded-[2rem] bg-white p-10 text-center shadow-xl ring-1 ring-stone-200">
          <h1 class="font-display text-4xl font-bold">Dein Warenkorb ist leer.</h1>
          <a class="focus-ring mt-6 inline-flex rounded-full bg-ink px-6 py-3 font-bold text-white hover:bg-clay" href="/#/">Weiter shoppen</a>
        </section>
      `;
      return;
    }
    this.innerHTML = `
      <section>
        <h1 class="font-display text-4xl font-bold">Kasse</h1>
        <div class="mt-6 grid gap-8 lg:grid-cols-[1fr_380px]">
          <form id="checkout-form" class="rounded-[2rem] bg-white p-6 shadow-xl ring-1 ring-stone-200 md:p-8">
            <h2 class="font-display text-2xl font-bold">Lieferadresse</h2>
            <div class="mt-5 grid gap-4 sm:grid-cols-2">
              ${this.input("name", "Name", "Max Mustermann")}
              ${this.input("email", "E-Mail", "max@example.de", "email")}
              ${this.input("street", "Strasse", "Hausweg 12")}
              ${this.input("zip", "PLZ", "10115")}
              ${this.input("city", "Stadt", "Berlin")}
              ${this.input("country", "Land", "Deutschland")}
            </div>
            <h2 class="mt-8 font-display text-2xl font-bold">Zahlung</h2>
            <div class="mt-4 grid gap-3 sm:grid-cols-2">
              <label class="rounded-2xl border border-stone-200 p-4 font-bold"><input class="mr-2" type="radio" name="payment_method" value="invoice" checked />Auf Rechnung</label>
              <label class="rounded-2xl border border-stone-200 p-4 font-bold"><input class="mr-2" type="radio" name="payment_method" value="credit_card_demo" />Kreditkarte (Demo)</label>
            </div>
            <button class="focus-ring mt-8 rounded-full bg-clay px-6 py-3 font-bold text-white shadow-lg hover:bg-[#9f4d2e]">Jetzt kaufen</button>
            <p id="message" class="mt-4 font-semibold text-red-700"></p>
          </form>
          <aside class="h-fit rounded-[2rem] bg-ink p-6 text-white shadow-xl">
            <h2 class="font-display text-2xl font-bold">Bestelluebersicht</h2>
            <div class="mt-5 space-y-4">
              ${this.cart.items.map((item) => `
                <div class="flex gap-3">
                  <img class="h-16 w-16 rounded-2xl object-cover" src="${item.image_url}" alt="${item.name}" />
                  <div class="flex-1 text-sm">
                    <p class="font-bold">${item.name}</p>
                    <p class="text-stone-300">Groesse ${item.size} · ${item.quantity}x</p>
                  </div>
                  <strong>${formatMoney(item.line_total, item.currency)}</strong>
                </div>
              `).join("")}
            </div>
            <div class="mt-6 border-t border-white/20 pt-4 flex justify-between text-lg"><span>Gesamt</span><strong>${formatMoney(this.cart.total)}</strong></div>
          </aside>
        </div>
      </section>
    `;
    this.querySelector("#checkout-form").addEventListener("submit", (event) => this.submit(event));
  }

  input(name, label, value, type = "text") {
    return `<label class="block text-sm font-bold">${label}<input required name="${name}" value="${value}" type="${type}" class="focus-ring mt-2 w-full rounded-2xl border border-stone-200 px-4 py-3" /></label>`;
  }

  async submit(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const message = this.querySelector("#message");
    try {
      const order = await shopFetch("/api/orders", {
        method: "POST",
        body: JSON.stringify({
          shipping: {
            name: form.get("name"),
            street: form.get("street"),
            zip: form.get("zip"),
            city: form.get("city"),
            country: form.get("country"),
            email: form.get("email"),
          },
          payment_method: form.get("payment_method"),
        }),
      });
      refreshCartBadge();
      window.location.hash = `#/order/${order.order_id}`;
    } catch (error) {
      message.textContent = error.message;
    }
  }
}

customElements.define("checkout-page", CheckoutPage);
