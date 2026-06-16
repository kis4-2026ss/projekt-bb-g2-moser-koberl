class ImprintPage extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <section class="max-w-3xl rounded-lg border border-zinc-200 bg-white p-6">
        <h1 class="mb-4 text-3xl font-bold">Impressum</h1>
        <p class="text-zinc-700">Sole Market GmbH</p>
        <p class="text-zinc-700">Musterstrasse 12</p>
        <p class="text-zinc-700">10115 Berlin</p>
        <p class="mt-4 text-zinc-700">E-Mail: service@sole-market.example</p>
        <p class="text-zinc-700">Telefon: +49 30 123456</p>
        <h2 class="mt-6 mb-2 text-xl font-bold">Vertreten durch</h2>
        <p class="text-zinc-700">Max Mustermann</p>
      </section>
    `;
  }
}

customElements.define("imprint-page", ImprintPage);
