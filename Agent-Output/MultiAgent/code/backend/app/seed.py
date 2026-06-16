"""Seed data for the e-commerce catalog."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal, init_db
from backend.app.models import Sneaker


SEED_SNEAKERS = [
    {
        "name": "Air Zoom Pulse",
        "brand": "Nike",
        "price": Decimal("129.99"),
        "currency": "EUR",
        "short_description": "Leichter Performance-Sneaker fuer den Alltag.",
        "long_description": (
            "Der Air Zoom Pulse kombiniert reaktionsfreudige Daempfung mit "
            "atmungsaktivem Mesh und einer griffigen Laufsohle."
        ),
        "image_url": "/static/images/air-zoom-pulse.jpg",
        "sizes": ["39", "40", "41", "42", "43", "44", "45"],
        "color": "White / Volt",
        "material": "Mesh, Synthetik, Gummi",
        "stock": 34,
        "rating": 4.6,
        "is_new": True,
    },
    {
        "name": "Ultraboost Street",
        "brand": "Adidas",
        "price": Decimal("159.95"),
        "currency": "EUR",
        "short_description": "Komfortabler Laufschuh mit Boost-Daempfung.",
        "long_description": (
            "Der Ultraboost Street bietet ein flexibles Primeknit-Obermaterial, "
            "stabile Fersenfuehrung und energierueckfuehrende Daempfung."
        ),
        "image_url": "/static/images/ultraboost-street.jpg",
        "sizes": ["38", "39", "40", "41", "42", "43", "44", "46"],
        "color": "Core Black",
        "material": "Primeknit, Textil, Continental-Gummi",
        "stock": 27,
        "rating": 4.8,
        "is_new": False,
    },
    {
        "name": "Classic Leather 85",
        "brand": "Reebok",
        "price": Decimal("89.90"),
        "currency": "EUR",
        "short_description": "Zeitloser Leder-Sneaker mit Retro-Silhouette.",
        "long_description": (
            "Der Classic Leather 85 setzt auf weiches Leder, eine gepolsterte "
            "Zwischensohle und ein reduziertes Design fuer jeden Tag."
        ),
        "image_url": "/static/images/classic-leather-85.jpg",
        "sizes": ["37", "38", "39", "40", "41", "42", "43", "44"],
        "color": "Chalk White",
        "material": "Leder, Textilfutter, Gummi",
        "stock": 48,
        "rating": 4.4,
        "is_new": False,
    },
    {
        "name": "Suede Vintage",
        "brand": "Puma",
        "price": Decimal("94.95"),
        "currency": "EUR",
        "short_description": "Klassischer Sneaker aus hochwertigem Wildleder.",
        "long_description": (
            "Der Suede Vintage liefert einen cleanen Court-Look mit weichem "
            "Wildleder-Obermaterial und robuster Cupsole."
        ),
        "image_url": "/static/images/suede-vintage.jpg",
        "sizes": ["38", "39", "40", "41", "42", "43", "44", "45"],
        "color": "Navy / White",
        "material": "Wildleder, Textil, Gummi",
        "stock": 22,
        "rating": 4.3,
        "is_new": True,
    },
    {
        "name": "Chuck 70 High",
        "brand": "Converse",
        "price": Decimal("99.99"),
        "currency": "EUR",
        "short_description": "High-Top Klassiker mit Premium-Canvas.",
        "long_description": (
            "Der Chuck 70 High bringt verstaerktes Canvas, Ortholite-Daempfung "
            "und ikonische Details in eine langlebige Alltagssilhouette."
        ),
        "image_url": "/static/images/chuck-70-high.jpg",
        "sizes": ["36", "37", "38", "39", "40", "41", "42", "43", "44"],
        "color": "Black / Egret",
        "material": "Canvas, Ortholite, Gummi",
        "stock": 51,
        "rating": 4.7,
        "is_new": False,
    },
    {
        "name": "Gel-City Runner",
        "brand": "ASICS",
        "price": Decimal("139.95"),
        "currency": "EUR",
        "short_description": "Stabiler Running-Sneaker fuer lange Tage.",
        "long_description": (
            "Der Gel-City Runner verbindet GEL-Daempfung im Rueckfussbereich "
            "mit einer stabilen Mittelsohle und belueftetem Obermaterial."
        ),
        "image_url": "/static/images/gel-city-runner.jpg",
        "sizes": ["39", "40", "41", "42", "43", "44", "45", "46"],
        "color": "Graphite Grey",
        "material": "Mesh, TPU, Gummi",
        "stock": 19,
        "rating": 4.5,
        "is_new": True,
    },
]


def seed_sneakers(db: Session) -> int:
    """Insert seed sneakers if they do not already exist."""
    inserted = 0

    for sneaker_data in SEED_SNEAKERS:
        existing = db.execute(
            select(Sneaker).where(
                Sneaker.name == sneaker_data["name"],
                Sneaker.brand == sneaker_data["brand"],
            )
        ).scalar_one_or_none()

        if existing is not None:
            continue

        db.add(Sneaker(**sneaker_data))
        inserted += 1

    db.commit()
    return inserted


def run_seed() -> int:
    """Initialize the database and seed catalog data."""
    init_db()

    with SessionLocal() as db:
        return seed_sneakers(db)


if __name__ == "__main__":
    created_count = run_seed()
    print(f"Seed complete. Inserted {created_count} sneakers.")
