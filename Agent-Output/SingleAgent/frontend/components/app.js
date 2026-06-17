import "./shell.js";
import "./product-list.js";
import "./product-detail.js";
import "./cart.js";
import "./checkout.js";
import "./order-confirmation.js";
import "./legal.js";

const app = document.querySelector("#app");

function route() {
  const hash = window.location.hash || "#/";
  const productMatch = hash.match(/^#\/product\/(\d+)$/);
  const orderMatch = hash.match(/^#\/order\/(\d+)$/);

  if (hash === "#/" || hash === "#") {
    app.innerHTML = `<product-list api-url="/api/products"></product-list>`;
    return;
  }
  if (productMatch) {
    app.innerHTML = `<product-detail product-id="${productMatch[1]}"></product-detail>`;
    return;
  }
  if (hash === "#/cart") {
    app.innerHTML = `<shopping-cart></shopping-cart>`;
    return;
  }
  if (hash === "#/checkout") {
    app.innerHTML = `<checkout-page></checkout-page>`;
    return;
  }
  if (orderMatch) {
    app.innerHTML = `<order-confirmation order-id="${orderMatch[1]}"></order-confirmation>`;
    return;
  }
  if (hash === "#/legal/imprint") {
    app.innerHTML = `<imprint-page></imprint-page>`;
    return;
  }
  if (hash === "#/legal/terms") {
    app.innerHTML = `<terms-page></terms-page>`;
    return;
  }
  if (hash === "#/legal/contact") {
    app.innerHTML = `<contact-page></contact-page>`;
    return;
  }
  app.innerHTML = `<not-found></not-found>`;
}

window.addEventListener("hashchange", route);
route();
