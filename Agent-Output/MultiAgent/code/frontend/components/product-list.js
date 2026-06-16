import { api, escapeHtml, formatMoney, placeholderImage } from "./api.js";

class ProductList extends HTMLElement {
  connectedCallback() {
    this.renderShell();
    this.loadProducts();
  }

  renderShell() {
    this.innerHTML = `
      <section class="mb-8 grid gap-4 md:grid-cols-[1.3fr_0.7fr] md:items-end">
        <div>
          <p class="mb-2 text-sm font-semibold uppercase tracking-normal text-teal-700">Neue Drops und Klassiker</p>
          <h1 class="max-w-3xl text-3xl font-bold tracking-normal text-zinc-950 sm:text-4xl md:text-5xl">Sneaker fuer Alltag, Training und Stadt.</h1>
        </div>
        <div class="grid gap-3 sm:grid-cols-[1fr_auto] md:justify-end">
          <input data-search class="focus-ring w-full rounded-md border border-zinc-300 bg-white px-3 py-2 md:w-64" placeholder="Suche" />
          <select data-brand class="focus-ring w-full rounded-md border border-zinc-300 bg-white px-3 py-2 sm:w-auto">
            <option value="">Alle Marken</option>
          </select>
        </div>
      </section>
      <section data-products class="grid gap-5 sm:grid-cols-2 lg:grid-cols-3"></section>
    `;
  }

  async loadProducts() {
    const grid = this.querySelector("[data-products]");
    grid.innerHTML = "<p class='text-zinc-600'>Produkte werden geladen...</p>";
    try {
      this.products = await api.get("/api/products");
      this.fillFilters();
      this.renderProducts();
      this.querySelector("[data-search]").addEventListener("input", () => this.renderProducts());
      this.querySelector("[data-brand]").addEventListener("change", () => this.renderProducts());
    } catch (error) {
      grid.innerHTML = `<p class="text-red-700">${error.message}</p>`;
    }
  }

  fillFilters() {
    const select = this.querySelector("[data-brand]");
    const brands = [...new Set(this.products.map((product) => product.brand))].sort();
    select.innerHTML += brands
      .map((brand) => `<option value="${escapeHtml(brand)}">${escapeHtml(brand)}</option>`)
      .join("");
  }

  renderProducts() {
    const search = this.querySelector("[data-search]").value.toLowerCase();
    const brand = this.querySelector("[data-brand]").value;
    const filtered = this.products.filter((product) => {
      const matchesSearch = `${product.brand} ${product.name}`.toLowerCase().includes(search);
      return matchesSearch && (!brand || product.brand === brand);
    });

    this.querySelector("[data-products]").innerHTML = filtered
      .map((product) => this.productCard(product))
      .join("") || "<p class='text-zinc-600'>Keine passenden Produkte gefunden.</p>";
  }

  productCard(product) {
    return `
      <article class="overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-sm">
        <a href="#/products/${product.id}" class="block">
          <img class="h-56 w-full bg-zinc-100 object-cover" src="${escapeHtml(product.image_url)}" alt="${escapeHtml(product.name)}" onerror="this.src='${placeholderImage(product.name)}'" />
        </a>
        <div class="p-4">
          <div class="mb-2 flex items-start justify-between gap-3">
            <div>
              <p class="text-sm font-semibold text-zinc-500">${escapeHtml(product.brand)}</p>
              <h2 class="text-lg font-bold">${escapeHtml(product.name)}</h2>
            </div>
            ${product.is_new ? "<span class='rounded bg-teal-100 px-2 py-1 text-xs font-bold text-teal-800'>Neu</span>" : ""}
          </div>
          <p class="min-h-12 text-sm text-zinc-600">${escapeHtml(product.short_description)}</p>
          <div class="mt-4 flex items-center justify-between">
            <span class="font-bold">${formatMoney(product.price, product.currency)}</span>
            <span class="text-sm text-zinc-600">${product.rating.toFixed(1)} / 5</span>
          </div>
        </div>
      </article>
    `;
  }
}

customElements.define("product-list", ProductList);
