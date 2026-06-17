import { formatMoney, friendlyError, refreshCartBadge, shopFetch, skeletonCards, stars } from "./api.js";

class ProductDetail extends HTMLElement {
  connectedCallback() {
    this.productId = this.getAttribute("product-id");
    this.quantity = 1;
    this.selectedSize = null;
    this.reviewRating = 5;
    this.innerHTML = skeletonCards(2);
    this.load();
  }

  async load() {
    try {
      const [product, reviews] = await Promise.all([
        shopFetch(`/api/products/${this.productId}`),
        shopFetch(`/api/products/${this.productId}/reviews`),
      ]);
      this.product = product;
      this.reviews = reviews;
      this.selectedSize = product.sizes[0];
      this.render();
    } catch (error) {
      this.innerHTML = friendlyError(error.message || "Dieses Produkt ist leider nicht mehr verfuegbar.");
    }
  }

  render() {
    const product = this.product;
    this.innerHTML = `
      <section class="grid gap-8 lg:grid-cols-2">
        <div class="overflow-hidden rounded-[2rem] bg-white shadow-xl ring-1 ring-stone-200">
          <img class="h-full max-h-[680px] w-full object-cover" src="${product.image_url}" alt="${product.name}" />
        </div>
        <div class="rounded-[2rem] bg-white/90 p-6 shadow-xl ring-1 ring-stone-200 md:p-8">
          <a href="/#/" class="focus-ring text-sm font-bold text-clay">Zurueck zum Shop</a>
          <p class="mt-6 text-sm font-bold uppercase tracking-[0.2em] text-clay">${product.brand}</p>
          <h1 class="mt-2 font-display text-4xl font-bold md:text-5xl">${product.name}</h1>
          <div class="mt-3 flex items-center gap-3 text-sm">
            <span>${stars(this.reviews.average_rating)}</span>
            <span class="font-semibold text-stone-600">${this.reviews.average_rating.toFixed(1)} · ${this.reviews.count} Reviews</span>
          </div>
          <p class="mt-5 text-lg text-stone-700">${product.long_description}</p>
          <dl class="mt-6 grid grid-cols-2 gap-3 text-sm">
            <div class="rounded-2xl bg-sand p-4"><dt class="font-bold">Farbe</dt><dd>${product.color}</dd></div>
            <div class="rounded-2xl bg-sand p-4"><dt class="font-bold">Material</dt><dd>${product.material}</dd></div>
            <div class="rounded-2xl bg-sand p-4"><dt class="font-bold">Bestand</dt><dd>${product.stock} Paar</dd></div>
            <div class="rounded-2xl bg-sand p-4"><dt class="font-bold">Preis</dt><dd class="font-display text-xl">${formatMoney(product.price, product.currency)}</dd></div>
          </dl>
          <div class="mt-7">
            <p class="mb-3 font-bold">Groesse waehlen</p>
            <div id="sizes" class="flex flex-wrap gap-2">
              ${product.sizes.map((size) => `<button data-size="${size}" class="focus-ring rounded-full border px-4 py-2 font-bold ${size === this.selectedSize ? "border-ink bg-ink text-white" : "border-stone-200 bg-white hover:bg-stone-100"}">${size}</button>`).join("")}
            </div>
          </div>
          <div class="mt-7 flex flex-wrap items-center gap-4">
            <div class="flex items-center rounded-full border border-stone-200 bg-white">
              <button id="minus" class="focus-ring px-4 py-3 font-bold">−</button>
              <span class="min-w-10 text-center font-bold">${this.quantity}</span>
              <button id="plus" class="focus-ring px-4 py-3 font-bold">+</button>
            </div>
            <button id="add" class="focus-ring rounded-full bg-clay px-6 py-3 font-bold text-white shadow-lg transition hover:-translate-y-0.5 hover:bg-[#9f4d2e]">In den Warenkorb</button>
          </div>
          <p id="notice" class="mt-4 hidden rounded-2xl bg-green-50 p-4 font-semibold text-green-800"></p>
        </div>
      </section>
      <section class="mt-10 rounded-[2rem] bg-white/90 p-6 shadow-xl ring-1 ring-stone-200 md:p-8">
        <div class="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 class="font-display text-3xl font-bold">Stimmen aus dem SneakerHaus</h2>
            <p class="text-stone-600">Teile deine Erfahrung mit diesem Modell.</p>
          </div>
        </div>
        <div class="mt-6 grid gap-6 lg:grid-cols-[1fr_0.9fr]">
          <div class="space-y-4">
            ${this.reviews.reviews.length ? this.reviews.reviews.map((review) => `
              <article class="rounded-3xl border border-stone-200 bg-white p-5">
                <div class="flex items-center justify-between gap-3">
                  <p class="font-bold">${review.author || "Gast"}</p>
                  <p class="text-xs text-stone-500">${new Date(review.created_at).toLocaleDateString("de-DE")}</p>
                </div>
                <div class="mt-2">${stars(review.rating)}</div>
                <p class="mt-3 text-stone-700">${review.comment}</p>
              </article>
            `).join("") : `<div class="rounded-3xl border border-stone-200 bg-white p-5">Noch keine Reviews. Sei die erste Stimme.</div>`}
          </div>
          <form id="review-form" class="rounded-3xl bg-sand p-5">
            <label class="block text-sm font-bold">Name optional<input name="author" class="focus-ring mt-2 w-full rounded-2xl border border-stone-200 px-4 py-3" maxlength="100" /></label>
            <div class="mt-4">
              <p class="mb-2 text-sm font-bold">Bewertung</p>
              <div id="rating" class="flex gap-1 text-3xl">${[1,2,3,4,5].map((value) => `<button type="button" data-rating="${value}" class="${value <= this.reviewRating ? "text-amber-500" : "text-stone-300"}">★</button>`).join("")}</div>
            </div>
            <label class="mt-4 block text-sm font-bold">Kommentar<textarea name="comment" required minlength="3" maxlength="1000" class="focus-ring mt-2 min-h-32 w-full rounded-2xl border border-stone-200 px-4 py-3"></textarea></label>
            <button class="focus-ring mt-4 rounded-full bg-ink px-6 py-3 font-bold text-white hover:bg-clay">Review senden</button>
            <p id="review-message" class="mt-3 text-sm font-semibold text-red-700"></p>
          </form>
        </div>
      </section>
    `;
    this.bindEvents();
  }

  bindEvents() {
    this.querySelectorAll("[data-size]").forEach((button) => button.addEventListener("click", () => {
      this.selectedSize = Number(button.dataset.size);
      this.render();
    }));
    this.querySelector("#minus").addEventListener("click", () => {
      this.quantity = Math.max(1, this.quantity - 1);
      this.render();
    });
    this.querySelector("#plus").addEventListener("click", () => {
      this.quantity += 1;
      this.render();
    });
    this.querySelector("#add").addEventListener("click", async () => {
      const notice = this.querySelector("#notice");
      try {
        await shopFetch("/api/cart/items", {
          method: "POST",
          body: JSON.stringify({ product_id: Number(this.productId), size: this.selectedSize, quantity: this.quantity }),
        });
        notice.className = "mt-4 rounded-2xl bg-green-50 p-4 font-semibold text-green-800";
        notice.textContent = "Zum Warenkorb hinzugefuegt.";
        refreshCartBadge();
      } catch (error) {
        notice.className = "mt-4 rounded-2xl bg-red-50 p-4 font-semibold text-red-800";
        notice.textContent = error.message;
      }
    });
    this.querySelectorAll("[data-rating]").forEach((button) => button.addEventListener("click", () => {
      this.reviewRating = Number(button.dataset.rating);
      this.render();
    }));
    this.querySelector("#review-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = new FormData(event.currentTarget);
      const message = this.querySelector("#review-message");
      try {
        await shopFetch(`/api/products/${this.productId}/reviews`, {
          method: "POST",
          body: JSON.stringify({
            author: form.get("author") || null,
            rating: this.reviewRating,
            comment: form.get("comment"),
          }),
        });
        await this.load();
      } catch (error) {
        message.textContent = error.message;
      }
    });
  }
}

customElements.define("product-detail", ProductDetail);
