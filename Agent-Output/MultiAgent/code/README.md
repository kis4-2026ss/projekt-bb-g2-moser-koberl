# Sole Market E-Commerce App

Sole Market ist eine vollstaendige Sneaker-E-Commerce-Demo mit FastAPI,
SQLAlchemy, SQLite und einem Frontend aus modularen Web Components. Die
Anwendung stellt Produktkatalog, Warenkorb, Checkout, Bestellbestaetigung,
Bewertungen sowie statische Informationsseiten bereit.

## Funktionen

- Produktuebersicht mit Sneaker-Katalog und Produktdetails
- Groessenwahl, Lagerbestandspruefung und Warenkorbverwaltung
- Checkout mit Lieferadresse und Zahlungsmethode
- Persistierte Bestellungen mit unveraenderlichen Artikel-Snapshots
- Produktbewertungen mit Durchschnittsbewertung
- Statische Seiten fuer Impressum, AGB und Kontakt
- FastAPI REST-API unter `/api`
- SQLite-Datenbank mit automatischer Tabellenanlage und Seed-Daten
- Frontend mit Vanilla JavaScript Web Components und Tailwind CSS

## Technischer Ueberblick

Das Backend liegt unter `backend/app` und verwendet FastAPI als HTTP-Schicht.
SQLAlchemy verwaltet die SQLite-Datenbank `ecommerce.sqlite3`. Beim Start
werden die Tabellen initialisiert und der Sneaker-Katalog wird befuellt, sofern
noch keine Produkte vorhanden sind.

Das Frontend liegt unter `frontend` und wird direkt von FastAPI als statische
Anwendung ausgeliefert. Die Navigation erfolgt hashbasiert im Browser, zum
Beispiel `#/products/1` oder `#/cart`.

Der Warenkorb wird absichtlich im Prozessspeicher gehalten. Die Architektur
definiert keine Warenkorb-Tabelle; persistiert werden Produkte, Bewertungen,
Bestellungen und Bestellpositionen.

## Projektstruktur

```text
backend/
  app/
    api/
      cart.py
      orders.py
      products.py
      reviews.py
    database.py
    main.py
    models.py
    schemas.py
    seed.py
frontend/
  components/
    api.js
    app.js
    checkout-page.js
    contact-page.js
    imprint-page.js
    not-found.js
    order-confirmation.js
    product-detail.js
    product-list.js
    shopping-cart.js
    terms-page.js
  styles/
    app.css
  index.html
tests/
requirements.txt
README.md
```

## Voraussetzungen

- Python 3.11 oder neuer
- `pip`
- Internetzugriff im Browser fuer das Tailwind-CDN

## Setup

Virtuelle Umgebung erstellen und aktivieren:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS oder Linux:

```bash
source .venv/bin/activate
```

Abhaengigkeiten installieren:

```bash
pip install -r requirements.txt
```

## Anwendung starten

```bash
uvicorn backend.app.main:app --reload
```

Danach ist die Anwendung erreichbar unter:

```text
http://127.0.0.1:8000/
```

Die interaktive API-Dokumentation ist erreichbar unter:

```text
http://127.0.0.1:8000/docs
```

Ein einfacher Healthcheck steht unter `/health` bereit.

## Frontend-Routen

- `#/` - Produktliste
- `#/products/{id}` - Produktdetailseite
- `#/cart` - Warenkorb
- `#/checkout` - Checkout
- `#/orders/{id}` - Bestellbestaetigung
- `#/imprint` - Impressum
- `#/terms` - AGB
- `#/contact` - Kontakt

## API-Endpunkte

### Produkte

| Methode | Pfad | Beschreibung |
| --- | --- | --- |
| `GET` | `/api/products` | Gibt alle Sneaker zurueck |
| `GET` | `/api/products/{id}` | Gibt einen Sneaker zurueck oder `404` |

### Warenkorb

| Methode | Pfad | Beschreibung |
| --- | --- | --- |
| `GET` | `/api/cart` | Gibt den aktuellen Warenkorb zurueck |
| `POST` | `/api/cart/items` | Legt eine Warenkorbposition an |
| `PATCH` | `/api/cart/items/{item_id}` | Aendert die Menge einer Position |
| `DELETE` | `/api/cart/items/{item_id}` | Entfernt eine Position |

Payload fuer `POST /api/cart/items`:

```json
{
  "product_id": 1,
  "size": "42",
  "quantity": 1
}
```

Payload fuer `PATCH /api/cart/items/{item_id}`:

```json
{
  "quantity": 2
}
```

### Bestellungen

| Methode | Pfad | Beschreibung |
| --- | --- | --- |
| `POST` | `/api/orders` | Erstellt eine Bestellung aus dem aktuellen Warenkorb |
| `GET` | `/api/orders/{id}` | Gibt eine Bestellung zurueck oder `404` |

Payload fuer `POST /api/orders`:

```json
{
  "shipping": {
    "name": "Max Mustermann",
    "street": "Musterstrasse 1",
    "zip": "10115",
    "city": "Berlin",
    "country": "Deutschland",
    "email": "max@example.com"
  },
  "payment_method": "credit_card"
}
```

### Bewertungen

| Methode | Pfad | Beschreibung |
| --- | --- | --- |
| `GET` | `/api/products/{id}/reviews` | Gibt Durchschnittsbewertung und Reviews zurueck |
| `POST` | `/api/products/{id}/reviews` | Erstellt eine Bewertung |

Payload fuer `POST /api/products/{id}/reviews`:

```json
{
  "author": "Max",
  "rating": 5,
  "comment": "Sehr bequem und sauber verarbeitet."
}
```

## Datenmodell

Die Anwendung verwendet folgende Tabellen:

- `sneakers`: Produktkatalog mit Preis, Waehrung, Beschreibungen, Bild-URL,
  verfuegbaren Groessen, Farbe, Material, Lagerbestand, Rating und Neu-Markierung.
- `reviews`: Kundenbewertungen mit Produktbezug, optionalem Autor, Rating,
  Kommentar und Erstellungszeitpunkt.
- `orders`: Bestellkopf mit Status, Lieferadresse, E-Mail, Zahlungsmethode,
  Zwischensumme und Gesamtbetrag.
- `order_items`: Bestellpositionen mit Produktbezug und Snapshots von Name,
  Marke, Preis und Bild-URL zum Zeitpunkt der Bestellung.

## Entwicklung

Backend-Code folgt PEP8-konformen Modulen mit Typannotationen und knappen
Docstrings. Pydantic-Schemas definieren die oeffentlichen Request- und
Response-Strukturen. Die Frontend-Komponenten sind einzeln in
`frontend/components` gekapselt und nutzen gemeinsame API-Helfer aus
`frontend/components/api.js`.

Die SQLite-Datei `ecommerce.sqlite3` wird im Projektverzeichnis angelegt.
Zum Zuruecksetzen der lokalen Datenbank kann die Datei im gestoppten Zustand
geloescht werden; sie wird beim naechsten Start neu erzeugt und wieder befuellt.

## Tests

Der Ordner `tests` ist fuer pytest-Tests vorgesehen. Falls Tests ergaenzt wurden,
koennen sie mit folgendem Befehl ausgefuehrt werden:

```bash
pytest
```

Falls `pytest` nicht installiert ist:

```bash
pip install pytest
```

## Beispielablauf

1. Anwendung starten.
2. Produkt auf der Startseite oeffnen.
3. Groesse und Menge waehlen und in den Warenkorb legen.
4. Warenkorb pruefen und Checkout oeffnen.
5. Lieferdaten eingeben und Bestellung abschliessen.
6. Bestellbestaetigung unter `#/orders/{id}` ansehen.
