import {
  api,
  escapeHtml,
  formatMoney,
  placeholderImage,
  setRoute,
} from "./api.js";

class ProductDetail extends HTMLElement {
  static get observedAttributes() {
    return ["product-id"];
  }

  connectedCallback() {
    const productId = Number(this.getAttribute("product-id"));
    if (productId && productId !== this._productId) {
      this.productId = productId;
    }
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (name === "product-id" && oldValue !== newValue && this.isConnected) {
      this.productId = Number(newValue);
    }
  }

  set productId(value) {
    this._productId = value;
    this.load();
  }

  async load() {
    if (!this._productId) {
      return;
    }
    this.innerHTML = "<p class='text-zinc-600'>Produkt wird geladen...</p>";
    try {
      const [product, reviewData] = await Promise.all([
        api.get(`/api/products/${this._productId}`),
        api.get(`/api/products/${this._productId}/reviews`),
      ]);
      this.product = product;
      this.reviewData = reviewData;
      this.render();
    } catch (error) {
      this.innerHTML = `<not-found message="${escapeHtml(error.message)}"></not-found>`;
    }
  }

  render() {
    this.innerHTML = `
      <section class="grid gap-8 lg:grid-cols-2">
        <img class="aspect-[4/3] w-full rounded-lg bg-zinc-100 object-cover" src="${escapeHtml(this.product.image_url)}" alt="${escapeHtml(this.product.name)}" onerror="this.src='${placeholderImage(this.product.name)}'" />
        <div>
          <a class="mb-4 inline-flex text-sm font-semibold text-teal-700 hover:text-teal-900" href="#/">Zurueck zum Shop</a>
          <p class="text-sm font-semibold uppercase tracking-normal text-zinc-500">${escapeHtml(this.product.brand)}</p>
          <h1 class="mt-1 text-3xl font-bold tracking-normal sm:text-4xl">${escapeHtml(this.product.name)}</h1>
          <p class="mt-3 text-lg text-zinc-700">${escapeHtml(this.product.long_description)}</p>
          <div class="mt-5 grid gap-3 text-sm sm:grid-cols-2">
            <span class="rounded-md border border-zinc-200 bg-white p-3"><b>Farbe</b><br />${escapeHtml(this.product.color)}</span>
            <span class="rounded-md border border-zinc-200 bg-white p-3"><b>Material</b><br />${escapeHtml(this.product.material)}</span>
            <span class="rounded-md border border-zinc-200 bg-white p-3"><b>Bestand</b><br />${this.product.stock}</span>
            <span class="rounded-md border border-zinc-200 bg-white p-3"><b>Bewertung</b><br />${this.product.rating.toFixed(1)} / 5</span>
          </div>
          <form data-cart-form class="mt-6 rounded-lg border border-zinc-200 bg-white p-4">
            <div class="mb-4 flex items-center justify-between">
              <span class="text-2xl font-bold">${formatMoney(this.product.price, this.product.currency)}</span>
              <span class="text-sm text-zinc-600">${this.product.currency}</span>
            </div>
            <label class="mb-3 block text-sm font-semibold">Groesse
              <select name="size" class="focus-ring mt-1 w-full rounded-md border border-zinc-300 px-3 py-2" required>
                ${this.product.sizes.map((size) => `<option value="${escapeHtml(size)}">${escapeHtml(size)}</option>`).join("")}
              </select>
            </label>
            <label class="mb-4 block text-sm font-semibold">Menge
              <input name="quantity" class="focus-ring mt-1 w-full rounded-md border border-zinc-300 px-3 py-2" type="number" min="1" max="${this.product.stock}" value="1" required />
            </label>
            <button class="focus-ring w-full rounded-md bg-zinc-950 px-4 py-3 font-bold text-white hover:bg-zinc-800" type="submit">In den Warenkorb</button>
            <p data-status class="mt-3 text-sm"></p>
          </form>
        </div>
      </section>
      <section class="mt-10 grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
        <form data-review-form class="rounded-lg border border-zinc-200 bg-white p-4">
          <h2 class="mb-4 text-xl font-bold">Bewertung schreiben</h2>
          <label class="mb-3 block text-sm font-semibold">Name
            <input name="author" class="focus-ring mt-1 w-full rounded-md border border-zinc-300 px-3 py-2" maxlength="120" />
          </label>
          <label class="mb-3 block text-sm font-semibold">Bewertung
            <select name="rating" class="focus-ring mt-1 w-full rounded-md border border-zinc-300 px-3 py-2">
              <option value="5">5 Sterne</option>
              <option value="4">4 Sterne</option>
              <option value="3">3 Sterne</option>
              <option value="2">2 Sterne</option>
              <option value="1">1 Stern</option>
            </select>
          </label>
          <label class="mb-4 block text-sm font-semibold">Kommentar
            <textarea name="comment" class="focus-ring mt-1 min-h-28 w-full rounded-md border border-zinc-300 px-3 py-2" required></textarea>
          </label>
          <button class="focus-ring w-full rounded-md bg-teal-700 px-4 py-2 font-bold text-white hover:bg-teal-800 sm:w-auto" type="submit">Absenden</button>
          <p data-review-status class="mt-3 text-sm"></p>
        </form>
        <div>
          <h2 class="mb-4 text-xl font-bold">Kundenbewertungen (${this.reviewData.reviews.length})</h2>
          <div data-reviews class="space-y-3">${this.renderReviews()}</div>
        </div>
      </section>
    `;
    this.bindEvents();
  }

  renderReviews() {
    if (!this.reviewData.reviews.length) {
      return "<p class='text-zinc-600'>Noch keine Bewertungen vorhanden.</p>";
    }
    return this.reviewData.reviews
      .map(
        (review) => `
          <article class="rounded-lg border border-zinc-200 bg-white p-4">
            <div class="mb-2 flex items-center justify-between gap-3">
              <strong>${escapeHtml(review.author || "Anonym")}</strong>
              <span class="text-sm text-zinc-600">${review.rating} / 5</span>
            </div>
            <p class="text-zinc-700">${escapeHtml(review.comment)}</p>
          </article>
        `
      )
      .join("");
  }

  bindEvents() {
    this.querySelector("[data-cart-form]").addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = new FormData(event.currentTarget);
      const status = this.querySelector("[data-status]");
      try {
        await api.post("/api/cart/items", {
          product_id: this.product.id,
          size: form.get("size"),
          quantity: Number(form.get("quantity")),
        });
        window.dispatchEvent(new CustomEvent("cart:changed"));
        status.className = "mt-3 text-sm text-teal-700";
        status.textContent = "Artikel wurde hinzugefuegt.";
        setTimeout(() => setRoute("/cart"), 450);
      } catch (error) {
        status.className = "mt-3 text-sm text-red-700";
        status.textContent = error.message;
      }
    });

    this.querySelector("[data-review-form]").addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = new FormData(event.currentTarget);
      const status = this.querySelector("[data-review-status]");
      try {
        await api.post(`/api/products/${this.product.id}/reviews`, {
          author: form.get("author") || null,
          rating: Number(form.get("rating")),
          comment: form.get("comment"),
        });
        status.className = "mt-3 text-sm text-teal-700";
        status.textContent = "Bewertung wurde gespeichert.";
        this.load();
      } catch (error) {
        status.className = "mt-3 text-sm text-red-700";
        status.textContent = error.message;
      }
    });
  }
}

customElements.define("product-detail", ProductDetail);
