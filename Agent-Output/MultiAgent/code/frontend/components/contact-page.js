class ContactPage extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <section class="grid gap-8 lg:grid-cols-[0.9fr_1.1fr]">
        <div>
          <h1 class="text-3xl font-bold">Kontakt</h1>
          <p class="mt-3 text-zinc-700">Unser Team beantwortet Fragen zu Produkten, Bestellungen und Ruecksendungen.</p>
          <div class="mt-6 space-y-2 text-zinc-700">
            <p><b>E-Mail:</b> service@sole-market.example</p>
            <p><b>Telefon:</b> +49 30 123456</p>
            <p><b>Adresse:</b> Musterstrasse 12, 10115 Berlin</p>
          </div>
        </div>
        <form data-contact-form class="rounded-lg border border-zinc-200 bg-white p-5">
          <label class="mb-4 block text-sm font-semibold">Name
            <input name="name" class="focus-ring mt-1 w-full rounded-md border border-zinc-300 px-3 py-2" required />
          </label>
          <label class="mb-4 block text-sm font-semibold">E-Mail
            <input name="email" type="email" class="focus-ring mt-1 w-full rounded-md border border-zinc-300 px-3 py-2" required />
          </label>
          <label class="mb-4 block text-sm font-semibold">Nachricht
            <textarea name="message" class="focus-ring mt-1 min-h-32 w-full rounded-md border border-zinc-300 px-3 py-2" required></textarea>
          </label>
          <button class="focus-ring w-full rounded-md bg-zinc-950 px-4 py-3 font-bold text-white sm:w-auto" type="submit">Nachricht senden</button>
          <p data-status class="mt-3 text-sm text-teal-700"></p>
        </form>
      </section>
    `;
    this.querySelector("[data-contact-form]").addEventListener("submit", (event) => {
      event.preventDefault();
      event.currentTarget.reset();
      this.querySelector("[data-status]").textContent = "Nachricht wurde erfasst.";
    });
  }
}

customElements.define("contact-page", ContactPage);
