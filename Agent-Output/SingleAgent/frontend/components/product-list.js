import { formatMoney, friendlyError, skeletonCards, stars } from "./api.js";

class ProductList extends HTMLElement {
  connectedCallback() {
    this.apiUrl = this.getAttribute("api-url") || "/api/products";
    this.products = [];
    this.brand = "Alle";
    this.search = "";
    this.sort = "new";
    this.renderShell();
    this.load();
  }

  renderShell() {
    this.innerHTML = `
      <section class="overflow-hidden rounded-[2rem] bg-ink text-white shadow-2xl">
        <div class="grid gap-8 p-8 md:grid-cols-[1.15fr_0.85fr] md:p-12">
          <div class="max-w-2xl">
            <p class="mb-4 inline-flex rounded-full bg-white/10 px-4 py-2 text-sm font-bold text-amber-100">Neue Drops, kuratiert fuer deinen Alltag</p>
            <h1 class="font-display text-5xl font-bold leading-tight md:text-7xl">Sneaker, die bewegen.</h1>
            <p class="mt-5 text-lg text-stone-200">Entdecke ausgewaehlte Runner, Court-Klassiker und Streetwear-Favoriten von SneakerHaus.</p>
            <button id="discover" class="focus-ring mt-8 rounded-full bg-clay px-6 py-3 font-bold text-white shadow-xl transition hover:-translate-y-1 hover:bg-[#9f4d2e]">Jetzt entdecken</button>
          </div>
          <div class="relative min-h-72 rounded-[2rem] bg-gradient-to-br from-clay via-[#d7a760] to-sage p-4">
            <div class="absolute inset-6 rounded-[2rem] border border-white/35"></div>
            <div class="absolute bottom-8 left-8 right-8 rounded-3xl bg-white/90 p-5 text-ink shadow-2xl">
              <p class="text-sm font-bold uppercase tracking-[0.2em] text-clay">SneakerHaus Edit</p>
              <p class="mt-2 font-display text-3xl font-bold">Komfort trifft Statement.</p>
            </div>
          </div>
        </div>
      </section>
      <section id="product-grid" class="mt-10">
        <div class="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h2 class="font-display text-3xl font-bold">Ausgewaehlte Sneaker</h2>
            <p class="mt-1 text-stone-600">Filtere nach Marke, Suche oder Sortierung.</p>
          </div>
          <div class="grid gap-3 sm:grid-cols-[1fr_auto]">
            <input id="search" class="focus-ring rounded-2xl border border-stone-200 bg-white px-4 py-3 shadow-sm" type="search" placeholder="Suche nach Modell oder Stil" />
            <select id="sort" class="focus-ring rounded-2xl border border-stone-200 bg-white px-4 py-3 font-semibold shadow-sm">
              <option value="new">Neu zuerst</option>
              <option value="price-asc">Preis aufsteigend</option>
              <option value="price-desc">Preis absteigend</option>
              <option value="rating">Bestbewertet</option>
            </select>
          </div>
        </div>
        <div id="brands" class="mb-6 flex flex-wrap gap-2"></div>
        <div id="products">${skeletonCards()}</div>
      </section>
    `;
    this.querySelector("#discover").addEventListener("click", () => this.querySelector("#product-grid").scrollIntoView());
    let timer;
    this.querySelector("#search").addEventListener("input", (event) => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        this.search = event.target.value.trim().toLowerCase();
        this.renderProducts();
      }, 250);
    });
    this.querySelector("#sort").addEventListener("change", (event) => {
      this.sort = event.target.value;
      this.renderProducts();
    });
  }

  async load() {
    try {
      const response = await fetch(this.apiUrl, { credentials: "same-origin" });
      this.products = await response.json();
      if (!response.ok) throw new Error();
      this.renderBrands();
      this.renderProducts();
    } catch {
      this.querySelector("#products").innerHTML = friendlyError("Unsere Sneaker-Auswahl ist gerade nicht erreichbar. Bitte versuche es spaeter erneut.");
    }
  }

  renderBrands() {
    const brands = ["Alle", ...new Set(this.products.map((product) => product.brand))];
    this.querySelector("#brands").innerHTML = brands.map((brand) => `
      <button data-brand="${brand}" class="focus-ring rounded-full px-4 py-2 text-sm font-bold transition ${brand === this.brand ? "bg-ink text-white" : "bg-white text-ink shadow-sm hover:bg-stone-100"}">${brand}</button>
    `).join("");
    this.querySelectorAll("[data-brand]").forEach((button) => {
      button.addEventListener("click", () => {
        this.brand = button.dataset.brand;
        this.renderBrands();
        this.renderProducts();
      });
    });
  }

  filteredProducts() {
    const filtered = this.products.filter((product) => {
      const matchesBrand = this.brand === "Alle" || product.brand === this.brand;
      const haystack = `${product.name} ${product.short_description}`.toLowerCase();
      return matchesBrand && (!this.search || haystack.includes(this.search));
    });
    return filtered.sort((a, b) => {
      if (this.sort === "price-asc") return Number(a.price) - Number(b.price);
      if (this.sort === "price-desc") return Number(b.price) - Number(a.price);
      if (this.sort === "rating") return Number(b.rating) - Number(a.rating);
      return Number(b.is_new) - Number(a.is_new) || a.name.localeCompare(b.name);
    });
  }

  renderProducts() {
    const products = this.filteredProducts();
    this.querySelector("#products").innerHTML = products.length ? `
      <div class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        ${products.map((product) => `
          <article class="group overflow-hidden rounded-3xl bg-white shadow-sm ring-1 ring-stone-200 transition duration-300 hover:-translate-y-1 hover:shadow-2xl">
            <a class="block focus-ring" href="/#/product/${product.id}">
              <div class="relative h-64 overflow-hidden bg-stone-100">
                <img class="h-full w-full object-cover transition duration-500 group-hover:scale-105" src="${product.image_url}" alt="${product.name}" loading="lazy" />
                ${product.is_new ? `<span class="absolute left-4 top-4 rounded-full bg-clay px-3 py-1 text-xs font-bold text-white shadow">Neu</span>` : ""}
              </div>
            </a>
            <div class="p-5">
              <p class="text-sm font-bold text-clay">${product.brand}</p>
              <h3 class="mt-1 font-display text-xl font-bold">${product.name}</h3>
              <p class="mt-2 line-clamp-2 min-h-11 text-sm text-stone-600">${product.short_description}</p>
              <div class="mt-4 flex items-center justify-between">
                <div class="text-sm" aria-label="${product.rating} von 5 Sternen">${stars(product.rating)}</div>
                <p class="font-display text-xl font-bold">${formatMoney(product.price, product.currency)}</p>
              </div>
              <a class="focus-ring mt-5 inline-flex w-full items-center justify-center rounded-full bg-ink px-4 py-3 text-sm font-bold text-white transition hover:bg-clay" href="/#/product/${product.id}">Details</a>
            </div>
          </article>
        `).join("")}
      </div>
    ` : `<div class="rounded-3xl bg-white p-8 text-center shadow-sm">Keine passenden Sneaker gefunden.</div>`;
  }
}

customElements.define("product-list", ProductList);
