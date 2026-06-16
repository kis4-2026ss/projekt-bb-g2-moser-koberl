"""FastAPI application entry point."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.app.api import cart, orders, products, reviews
from backend.app.database import SessionLocal, init_db
from backend.app.seed import seed_sneakers


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"

app = FastAPI(title="Sneaker E-Commerce API")
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(reviews.router)


@app.on_event("startup")
def on_startup() -> None:
    """Create database tables and seed the initial product catalog."""
    init_db()
    with SessionLocal() as db:
        seed_sneakers(db)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Return basic service health information."""
    return {"status": "ok"}


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
