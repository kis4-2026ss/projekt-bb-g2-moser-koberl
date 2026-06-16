const JSON_HEADERS = { "Content-Type": "application/json" };

export const api = {
  async get(path) {
    return request(path);
  },

  async post(path, payload) {
    return request(path, {
      method: "POST",
      headers: JSON_HEADERS,
      body: JSON.stringify(payload),
    });
  },

  async patch(path, payload) {
    return request(path, {
      method: "PATCH",
      headers: JSON_HEADERS,
      body: JSON.stringify(payload),
    });
  },

  async delete(path) {
    return request(path, { method: "DELETE" });
  },
};

async function request(path, options = {}) {
  const response = await fetch(path, options);
  if (response.status === 204) {
    return null;
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Die Anfrage konnte nicht verarbeitet werden.");
  }
  return data;
}

export function formatMoney(value, currency = "EUR") {
  return new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency,
  }).format(Number(value || 0));
}

export function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

export function placeholderImage(label) {
  const cleanLabel = escapeHtml(label || "Sneaker");
  return (
    "data:image/svg+xml;charset=UTF-8," +
    encodeURIComponent(`
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 560">
        <rect width="800" height="560" fill="#f4f4f5"/>
        <path d="M145 360c75-8 118-38 162-91 52 54 121 89 260 103 44 4 86 17 108 44 13 16 5 40-15 45-165 42-355 43-543 9-27-5-38-39-17-58 12-11 27-19 45-52z" fill="#18181b"/>
        <path d="M308 269c50 45 120 76 259 90 42 4 79 16 101 39-115 18-290 18-454-4 43-29 70-69 94-125z" fill="#14b8a6"/>
        <text x="400" y="126" text-anchor="middle" font-family="Arial, sans-serif" font-size="44" font-weight="700" fill="#18181b">${cleanLabel}</text>
      </svg>
    `)
  );
}

export function setRoute(route) {
  window.location.hash = route;
}

export function currentRoute() {
  return window.location.hash.replace(/^#/, "") || "/";
}
