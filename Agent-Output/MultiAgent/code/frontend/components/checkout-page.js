import { api, escapeHtml, formatMoney, setRoute } from "./api.js";

class CheckoutPage extends HTMLElement {
  connectedCallback() {
    this.load();
  }

  async load() {
    this.innerHTML = "<p class='text-zinc-600'>Checkout wird geladen...</p>";
    try {
      this.cart = await api.get("/api/cart");
      this.render();
    } catch (error) {
      this.innerHTML = `<p class="text-red-700">${error.message}</p>`;
    }
  }

  render() {
    if (!this.cart.items.length) {
      this.innerHTML = "<shopping-cart></shopping-cart>";
      return;
    }
    this.innerHTML = `
      <section class="grid gap-8 lg:grid-cols-[1fr_360px]">
        <form data-checkout-form class="rounded-lg border border-zinc-200 bg-white p-5">
          <h1 class="mb-5 text-3xl font-bold">Checkout</h1>
          <div class="grid gap-4 sm:grid-cols-2">
            ${this.input("name", "Name")}
            ${this.input("email", "E-Mail", "email")}
            ${this.input("street", "Strasse", "text", "sm:col-span-2")}
            ${this.input("zip", "PLZ")}
            ${this.input("city", "Stadt")}
            ${this.input("country", "Land", "text", "", "Deutschland")}
            <label class="block text-sm font-semibold sm:col-span-2">Zahlungsart
              <select name="payment_method" class="focus-ring mt-1 w-full rounded-md border border-zinc-300 px-3 py-2">
                <option value="credit_card">Kreditkarte</option>
                <option value="paypal">PayPal</option>
                <option value="invoice">Rechnung</option>
              </select>
            </label>
          </div>
          <button class="focus-ring mt-6 w-full rounded-md bg-zinc-950 px-5 py-3 font-bold text-white hover:bg-zinc-800 sm:w-auto" type="submit">Bestellung abschliessen</button>
          <p data-status class="mt-3 text-sm"></p>
        </form>
        <aside class="h-fit rounded-lg border border-zinc-200 bg-white p-5">
          <h2 class="mb-4 text-xl font-bold">Bestellung</h2>
          <div class="space-y-3">
            ${this.cart.items
              .map(
                (item) => `
                  <div class="flex justify-between gap-4 text-sm">
                    <span class="min-w-0 break-words">${item.quantity}x ${escapeHtml(item.name)}, ${escapeHtml(item.size)}</span>
                    <span class="shrink-0">${formatMoney(item.line_total, item.currency)}</span>
                  </div>
                `
              )
              .join("")}
          </div>
          <div class="mt-5 flex justify-between border-t border-zinc-200 pt-4 text-lg font-bold">
            <span>Gesamt</span><span>${formatMoney(this.cart.total, this.cart.currency)}</span>
          </div>
        </aside>
      </section>
    `;
    this.querySelector("[data-checkout-form]").addEventListener("submit", (event) => this.submit(event));
  }

  input(name, label, type = "text", classes = "", value = "") {
    return `
      <label class="block text-sm font-semibold ${classes}">${label}
        <input name="${name}" type="${type}" value="${value}" class="focus-ring mt-1 w-full rounded-md border border-zinc-300 px-3 py-2" required />
      </label>
    `;
  }

  async submit(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const status = this.querySelector("[data-status]");
    try {
      const order = await api.post("/api/orders", {
        shipping: {
          name: form.get("name"),
          street: form.get("street"),
          zip: form.get("zip"),
          city: form.get("city"),
          country: form.get("country"),
          email: form.get("email"),
        },
        payment_method: form.get("payment_method"),
      });
      window.dispatchEvent(new CustomEvent("cart:changed"));
      setRoute(`/orders/${order.order_id}`);
    } catch (error) {
      status.className = "mt-3 text-sm text-red-700";
      status.textContent = error.message;
    }
  }
}

customElements.define("checkout-page", CheckoutPage);
