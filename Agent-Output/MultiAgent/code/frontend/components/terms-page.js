class TermsPage extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <section class="max-w-3xl rounded-lg border border-zinc-200 bg-white p-6">
        <h1 class="mb-4 text-3xl font-bold">Allgemeine Geschaeftsbedingungen</h1>
        <h2 class="mt-5 mb-2 text-xl font-bold">1. Geltungsbereich</h2>
        <p class="text-zinc-700">Diese Bedingungen gelten fuer alle Bestellungen im Sole Market Demo-Shop.</p>
        <h2 class="mt-5 mb-2 text-xl font-bold">2. Vertragsschluss</h2>
        <p class="text-zinc-700">Mit Abschluss des Checkouts wird eine Bestellung im System angelegt.</p>
        <h2 class="mt-5 mb-2 text-xl font-bold">3. Preise und Zahlung</h2>
        <p class="text-zinc-700">Alle Preise werden in Euro ausgewiesen. Die verfuegbaren Zahlungsarten werden im Checkout angezeigt.</p>
        <h2 class="mt-5 mb-2 text-xl font-bold">4. Lieferung</h2>
        <p class="text-zinc-700">Die Lieferung erfolgt an die im Checkout angegebene Adresse.</p>
      </section>
    `;
  }
}

customElements.define("terms-page", TermsPage);
