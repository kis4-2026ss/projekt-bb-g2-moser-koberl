# SneakerHaus

SneakerHaus ist ein kleiner, verkaufsfertiger Sneaker-Shop als Demo-Produkt: moderne Produktuebersicht, Detailseiten, Reviews, Warenkorb, Checkout und Bestellbestaetigung in einem stimmigen Markenauftritt.

## Features

- Kuratierte Sneaker-Auswahl mit Markenfilter, Suche und Sortierung
- Produktdetailseiten mit Groessenauswahl, Mengen-Stepper und Reviews
- Persistenter Warenkorb pro Besuch
- Checkout mit Lieferadresse und Demo-Zahlungsarten
- Bestellbestaetigung mit Positionen, Adresse und Gesamtsumme
- Impressum, AGB/Widerruf und Kontaktseite mit fiktiven Inhalten

## Setup

```powershell
pip install -r requirements.txt
```

## Start

```powershell
uvicorn backend.app.main:app --reload
```

Danach ist SneakerHaus unter `http://127.0.0.1:8000/` erreichbar.

Beim ersten Start wird automatisch eine SQLite-Datenbank unter `./data/shop.db` angelegt und mit Sneaker-Daten gefuellt. Der Datenbankpfad kann ueber `SNEAKERHAUS_DATABASE_URL` angepasst werden, zum Beispiel:

```powershell
$env:SNEAKERHAUS_DATABASE_URL="sqlite:///./data/shop.db"
```

## Tests

```powershell
pytest
```

Mit Coverage-Bericht:

```powershell
pytest --cov=backend --cov-report=term-missing --cov-report=html --cov-fail-under=90
```

Der HTML-Bericht wird unter `htmlcov/` erzeugt.

## Projektstruktur

```text
backend/app/main.py
backend/app/database.py
backend/app/models.py
backend/app/schemas.py
backend/app/api/
backend/app/seed.py
frontend/index.html
frontend/components/
frontend/styles/
tests/
requirements.txt
README.md
```
