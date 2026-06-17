export const formatMoney = (value, currency = "EUR") =>
  new Intl.NumberFormat("de-DE", { style: "currency", currency }).format(Number(value));

export const stars = (rating = 0) => {
  const rounded = Math.round(Number(rating));
  return Array.from({ length: 5 }, (_, index) =>
    `<span class="${index < rounded ? "text-amber-500" : "text-stone-300"}">★</span>`
  ).join("");
};

export async function shopFetch(url, options = {}) {
  const response = await fetch(url, {
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data?.error?.message || "Das hat leider nicht geklappt. Bitte versuche es erneut.");
  }
  return data;
}

export async function refreshCartBadge() {
  try {
    const cart = await shopFetch("/api/cart");
    window.dispatchEvent(new CustomEvent("cart-updated", { detail: cart }));
  } catch {
    window.dispatchEvent(new CustomEvent("cart-updated", { detail: { item_count: 0 } }));
  }
}

export const skeletonCards = (count = 8) => `
  <div class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
    ${Array.from({ length: count }, () => `
      <div class="overflow-hidden rounded-3xl bg-white/75 shadow-sm ring-1 ring-stone-200">
        <div class="h-56 animate-pulse bg-stone-200"></div>
        <div class="space-y-3 p-5">
          <div class="h-4 w-1/3 animate-pulse rounded bg-stone-200"></div>
          <div class="h-6 w-3/4 animate-pulse rounded bg-stone-200"></div>
          <div class="h-4 w-full animate-pulse rounded bg-stone-200"></div>
          <div class="h-10 w-full animate-pulse rounded-full bg-stone-200"></div>
        </div>
      </div>
    `).join("")}
  </div>
`;

export const friendlyError = (message) => `
  <div class="rounded-3xl border border-red-200 bg-red-50 p-6 text-red-900 shadow-sm">
    ${message || "Im Moment koennen wir diese Ansicht nicht anzeigen. Bitte versuche es gleich noch einmal."}
  </div>
`;
