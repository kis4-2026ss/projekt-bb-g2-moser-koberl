from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import Product, Review


PRODUCTS = [
    {
        "id": 1,
        "name": "Air Pulse Runner",
        "brand": "Nike",
        "price": Decimal("129.90"),
        "currency": "EUR",
        "short_description": "Leichter City-Runner mit federnder Daempfung.",
        "long_description": "Der Air Pulse Runner verbindet atmungsaktives Mesh mit einer reaktiven Sohle fuer lange Tage in der Stadt. Der cleane Look passt zu Denim, Techwear und Wochenend-Outfits.",
        "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=1200&q=80",
        "sizes": [40, 41, 42, 43, 44, 45],
        "color": "Signalrot / Weiss",
        "material": "Mesh, Synthetik, Gummi",
        "stock": 18,
        "rating": 4.7,
        "is_new": True,
    },
    {
        "id": 2,
        "name": "Forum Street Low",
        "brand": "Adidas",
        "price": Decimal("109.95"),
        "currency": "EUR",
        "short_description": "Retro-Basketball-Silhouette fuer jeden Tag.",
        "long_description": "Der Forum Street Low bringt Court-DNA in deinen Alltag. Gepolsterter Einstieg, griffige Cupsole und weiches Obermaterial sorgen fuer Komfort ohne Kompromisse.",
        "image_url": "https://images.unsplash.com/photo-1608231387042-66d1773070a5?auto=format&fit=crop&w=1200&q=80",
        "sizes": [39, 40, 41, 42, 43, 44, 46],
        "color": "Creme / Navy",
        "material": "Leder, Textilfutter, Gummi",
        "stock": 24,
        "rating": 4.5,
        "is_new": False,
    },
    {
        "id": 3,
        "name": "574 Heritage Moss",
        "brand": "New Balance",
        "price": Decimal("119.90"),
        "currency": "EUR",
        "short_description": "Klassischer Dad-Sneaker mit weicher EVA-Zwischensohle.",
        "long_description": "Der 574 Heritage Moss kombiniert Wildleder-Overlays, robustes Nylon und eine stabile Laufsohle. Ein zeitloser Sneaker fuer Pendeln, Reisen und entspannte Office-Looks.",
        "image_url": "https://images.unsplash.com/photo-1539185441755-769473a23570?auto=format&fit=crop&w=1200&q=80",
        "sizes": [40, 41, 42, 43, 44, 45, 46],
        "color": "Moosgruen / Grau",
        "material": "Wildleder, Nylon, EVA",
        "stock": 16,
        "rating": 4.8,
        "is_new": True,
    },
    {
        "id": 4,
        "name": "Suede Terrace",
        "brand": "Puma",
        "price": Decimal("89.95"),
        "currency": "EUR",
        "short_description": "Weicher Suede-Look mit flacher Gum-Sohle.",
        "long_description": "Der Suede Terrace ist reduziert, bequem und vielseitig. Die flache Gummisohle gibt sicheren Halt, waehrend das samtige Obermaterial dem Outfit Tiefe gibt.",
        "image_url": "https://images.unsplash.com/photo-1600185365483-26d7a4cc7519?auto=format&fit=crop&w=1200&q=80",
        "sizes": [38, 39, 40, 41, 42, 43, 44],
        "color": "Cognac / Gum",
        "material": "Wildleder, Textil, Gummi",
        "stock": 31,
        "rating": 4.3,
        "is_new": False,
    },
    {
        "id": 5,
        "name": "Gel Metro Knit",
        "brand": "Asics",
        "price": Decimal("139.90"),
        "currency": "EUR",
        "short_description": "Technischer Sneaker mit stabilem Laufgefuehl.",
        "long_description": "Der Gel Metro Knit ist fuer lange Wege gebaut: flexible Strickzonen, seitliche Stabilisierung und komfortable Daempfung machen ihn zum Favoriten fuer aktive Tage.",
        "image_url": "https://images.unsplash.com/photo-1595341888016-a392ef81b7de?auto=format&fit=crop&w=1200&q=80",
        "sizes": [40, 41, 42, 43, 44, 45],
        "color": "Schwarz / Silber",
        "material": "Knit, TPU, Gummi",
        "stock": 12,
        "rating": 4.6,
        "is_new": True,
    },
    {
        "id": 6,
        "name": "Club C Chalk",
        "brand": "Reebok",
        "price": Decimal("84.90"),
        "currency": "EUR",
        "short_description": "Minimalistischer Court-Sneaker in warmem Weiss.",
        "long_description": "Der Club C Chalk setzt auf klare Linien, ein weiches Tragegefuehl und dezente Details. Ideal fuer alle, die einen ruhigen Sneaker mit Premium-Anmutung suchen.",
        "image_url": "https://images.unsplash.com/photo-1603808033192-082d6919d3e1?auto=format&fit=crop&w=1200&q=80",
        "sizes": [37, 38, 39, 40, 41, 42, 43],
        "color": "Chalk / Gruen",
        "material": "Leder, Frottee-Futter, Gummi",
        "stock": 27,
        "rating": 4.4,
        "is_new": False,
    },
    {
        "id": 7,
        "name": "Chuck Urban High",
        "brand": "Converse",
        "price": Decimal("79.95"),
        "currency": "EUR",
        "short_description": "Canvas-High-Top mit ikonischer Silhouette.",
        "long_description": "Der Chuck Urban High bleibt nah am Original und fuehlt sich trotzdem frisch an. Canvas, Zehenkappe und flexible Sohle machen ihn zum unkomplizierten Alltagsbegleiter.",
        "image_url": "https://images.unsplash.com/photo-1607522370275-f14206abe5d3?auto=format&fit=crop&w=1200&q=80",
        "sizes": [38, 39, 40, 41, 42, 43, 44, 45],
        "color": "Schwarz / Weiss",
        "material": "Canvas, Gummi",
        "stock": 34,
        "rating": 4.2,
        "is_new": False,
    },
    {
        "id": 8,
        "name": "Jazz Court Olive",
        "brand": "Saucony",
        "price": Decimal("99.90"),
        "currency": "EUR",
        "short_description": "Vintage-Runner mit griffiger Profilsohle.",
        "long_description": "Der Jazz Court Olive mixt Retro-Running mit moderner Alltagstauglichkeit. Die profilierte Sohle, das weiche Obermaterial und die ausgewogene Passform ueberzeugen vom ersten Schritt an.",
        "image_url": "https://images.unsplash.com/photo-1605348532760-6753d2c43329?auto=format&fit=crop&w=1200&q=80",
        "sizes": [39, 40, 41, 42, 43, 44, 45],
        "color": "Olive / Sand",
        "material": "Nylon, Wildleder, EVA",
        "stock": 21,
        "rating": 4.5,
        "is_new": True,
    },
]

REVIEWS = [
    (1, "Mara", 5, "Sehr bequem und optisch noch besser als erwartet."),
    (1, "Jonas", 4, "Guter Halt, faellt bei mir normal aus."),
    (3, "Lea", 5, "Perfekter Sneaker fuer lange Tage im Buero."),
    (5, "Timo", 5, "Die Daempfung ist stark, besonders auf Asphalt."),
    (7, "Nina", 4, "Klassiker, passt zu fast allem."),
]


def seed_db(db: Session) -> None:
    existing = db.scalar(select(Product.id).limit(1))
    if existing:
        return

    products = [Product(**item) for item in PRODUCTS]
    db.add_all(products)
    db.flush()
    db.add_all(
        Review(product_id=product_id, author=author, rating=rating, comment=comment)
        for product_id, author, rating, comment in REVIEWS
    )
    db.commit()
