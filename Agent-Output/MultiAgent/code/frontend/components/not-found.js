import { escapeHtml } from "./api.js";

class NotFound extends HTMLElement {
  connectedCallback() {
    const message = this.getAttribute("message") || "Die angeforderte Seite wurde nicht gefunden.";
    this.innerHTML = `
      <section class="rounded-lg border border-zinc-200 bg-white p-8 text-center">
        <h1 class="text-3xl font-bold">404</h1>
        <p class="mt-2 text-zinc-700">${escapeHtml(message)}</p>
        <a class="mt-5 inline-flex rounded-md bg-zinc-950 px-4 py-3 font-bold text-white" href="#/">Zum Shop</a>
      </section>
    `;
  }
}

customElements.define("not-found", NotFound);
