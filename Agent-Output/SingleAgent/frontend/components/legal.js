class ImprintPage extends HTMLElement {
  connectedCallback() {
    this.innerHTML = legalShell("Impressum", `
      <p><strong>SneakerHaus GmbH</strong><br>Fiktive Handelsgesellschaft fuer Sneaker<br>Hausallee 24<br>10115 Berlin<br>Deutschland</p>
      <p><strong>Vertreten durch:</strong> Mara Schneider und Leon Bauer</p>
      <p><strong>Kontakt:</strong><br>E-Mail: hallo@sneakerhaus.example<br>Telefon: +49 30 1234567</p>
      <p><strong>Registereintrag:</strong><br>Amtsgericht Berlin-Charlottenburg, HRB 123456 B</p>
      <p><strong>Umsatzsteuer-ID:</strong> DE123456789</p>
    `);
  }
}

class TermsPage extends HTMLElement {
  connectedCallback() {
    this.innerHTML = legalShell("AGB & Widerruf", `
      <ul class="list-disc space-y-3 pl-5">
        <li>Alle Angebote in diesem Demo-Shop sind freibleibend und dienen der realistischen Produktpraesentation.</li>
        <li>Preise verstehen sich inklusive gesetzlicher Umsatzsteuer. Der Versand ist in dieser Demo kostenfrei.</li>
        <li>Du kannst ungetragene Ware innerhalb von 14 Tagen nach Erhalt widerrufen.</li>
        <li>Die Rueckzahlung erfolgt ueber die im Bestellprozess gewaählte Demo-Zahlungsart.</li>
        <li>Fuer Fragen zu Groessen, Pflege oder Retouren hilft dir unser fiktives SneakerHaus-Team gern weiter.</li>
      </ul>
    `);
  }
}

class ContactPage extends HTMLElement {
  connectedCallback() {
    this.innerHTML = legalShell("Kontakt", `
      <p>Schreib uns, wenn du Fragen zu Produkten, Groessen oder deiner Bestellung hast.</p>
      <form id="contact-form" class="mt-6 grid gap-4">
        <label class="text-sm font-bold">Name<input required class="focus-ring mt-2 w-full rounded-2xl border border-stone-200 px-4 py-3" /></label>
        <label class="text-sm font-bold">E-Mail<input required type="email" class="focus-ring mt-2 w-full rounded-2xl border border-stone-200 px-4 py-3" /></label>
        <label class="text-sm font-bold">Nachricht<textarea required class="focus-ring mt-2 min-h-32 w-full rounded-2xl border border-stone-200 px-4 py-3"></textarea></label>
        <button class="focus-ring w-fit rounded-full bg-ink px-6 py-3 font-bold text-white hover:bg-clay">Senden</button>
        <p id="thanks" class="font-semibold text-green-800"></p>
      </form>
    `);
    this.querySelector("#contact-form").addEventListener("submit", (event) => {
      event.preventDefault();
      event.currentTarget.reset();
      this.querySelector("#thanks").textContent = "Vielen Dank, wir melden uns.";
    });
  }
}

class NotFound extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <section class="rounded-[2rem] bg-white p-10 text-center shadow-xl ring-1 ring-stone-200">
        <p class="font-bold text-clay">Nicht gefunden</p>
        <h1 class="mt-2 font-display text-4xl font-bold">Diese Seite gibt es im SneakerHaus nicht.</h1>
        <p class="mt-3 text-stone-600">Vielleicht wartet dein neues Paar schon im Shop.</p>
        <a class="focus-ring mt-6 inline-flex rounded-full bg-ink px-6 py-3 font-bold text-white hover:bg-clay" href="/#/">Zum Shop</a>
      </section>
    `;
  }
}

function legalShell(title, content) {
  return `
    <section class="mx-auto max-w-3xl rounded-[2rem] bg-white p-6 shadow-xl ring-1 ring-stone-200 md:p-10">
      <a href="/#/" class="focus-ring text-sm font-bold text-clay">Zurueck zum Shop</a>
      <h1 class="mt-6 font-display text-4xl font-bold">${title}</h1>
      <div class="mt-6 space-y-4 leading-7 text-stone-700">${content}</div>
    </section>
  `;
}

customElements.define("imprint-page", ImprintPage);
customElements.define("terms-page", TermsPage);
customElements.define("contact-page", ContactPage);
customElements.define("not-found", NotFound);
