# Ergebnisse

## Ausführung

| | Multi-Agent System | Single-Agent System |
|---|---|---|
| **Werkzeug** | `codex_orchestrator_multi_agent.py` (LangGraph-Orchestrator mit PO / Architect / Developer / Tester / Reviewer) | Codex CLI direkt (`codex exec`) |
| **Modell** | GPT-5.5 | GPT-5.5 |
| **Ausführungen** | 1 (inkl. automatischem Korrekturlauf durch den Reviewer) | 2 (1. Lauf: App-Code; 2. Lauf: Tests, da der Agent im ersten Lauf keine Tests erstellt hat) |

Der Multi-Agent-Orchestrator koordiniert automatisch fünf spezialisierte Rollen über einen LangGraph-Graphen: Der Product Owner erstellt Anforderungen, der Architect zerlegt sie in Work Items, der Developer implementiert sie via Codex CLI, der Tester schreibt Tests ebenfalls via Codex CLI, und der Reviewer bewertet das Ergebnis – bei einem „Fail"-Urteil wird automatisch ein Korrekturlauf angestoßen. Das Single-Agent-System übergibt den vollständigen Anforderungstext direkt in einer Codex-CLI-Session. Da der Agent im ersten Lauf keine Tests implementiert hat, war eine zweite manuelle Ausführung mit expliziter Anweisung zur Testerstellung notwendig.

---

## Multi-Agent System

### Codequalität
#### Backend:
- Der Code ist modular aufgebaut nach dem Prinzip "Separation of Concerns" – mit eigenen Dateien für `main.py`, `database.py`, `models.py`, `schemas.py` und `seed.py`
- Die API-Endpunkte sind thematisch in ein eigenes Verzeichnis `/app/api` unterteilt (products, cart, orders, reviews)
- Es wird das **veraltete** `@app.on_event("startup")` verwendet – beim Ausführen der Tests werden 16 Deprecation-Warnungen ausgegeben; FastAPI empfiehlt hier seit längerer Zeit den `lifespan`-Kontext-Manager
- Ebenfalls deprecated: `datetime.utcnow()` in den Modellen – auch dafür werden Warnungen generiert
- Die Datenbankmodelle verwenden `CheckConstraint` für Wertebereichsvalidierung (z.B. Preis ≥ 0, Rating 0–5) – gute Datenbankabsicherung
- Der Warenkorb wird **in-memory** gespeichert (Python-Dict `_cart_items` in `cart.py`), nicht in der Datenbank – der Warenkorbinhalt geht bei einem Server-Neustart verloren
- API-Dokumentationsrouten (`/docs`, `/redoc`) sind nicht deaktiviert – sie sind im laufenden System erreichbar
- Fehlerbehandlung: `HTTPException` wird geworfen, Fehlermeldungen sind jedoch intern formuliert (z.B. `"detail": "Product not found"`) ohne ein einheitliches, nach außen abgesichertes Fehlerformat

#### Frontend
- Das Frontend wurde in Web Components unterteilt: `product-list`, `product-detail`, `shopping-cart`, `checkout-page`, `order-confirmation` sowie Legal-Pages und eine `not-found`-Seite
- Gemeinsame Hilfsfunktionen für API-Calls, Geldformatierung und Platzhalterbilder wurden in `api.js` ausgelagert
- Es wird `escapeHtml` zur Ausgabe von Benutzerdaten verwendet – gute Absicherung gegen XSS
- Das Design ist funktional und klar, aber weniger aufwändig gestaltet als beim Single-Agent-System (kein eigenes Branding, keine Custom-Farben im Theme)

### Produktqualität
- Der Output hat auf Anhieb kompiliert und gestartet
- Das Design ist funktional und schlicht (Tailwind mit Standard-Farben)
- Produktübersicht mit Markenfilter und Suche funktioniert
- Produktdetailseite funktioniert
- Warenkorb funktioniert (solange der Server nicht neu gestartet wird – In-Memory-Speicher)
- Bestellabschluss funktioniert
- Bestelldetailseite funktioniert
- Bewertungsfunktion funktioniert
- Kontaktseite, Impressum und AGB vorhanden
- Inputvalidierung nicht vollständig: z.B. wird beim Checkout eine Postleitzahl als beliebiger String akzeptiert; es fehlt ein zentrales Fehlerformat für den Client

### Funktionale Korrektheit (bestehende Unit Tests)
- Alle 72 (von der KI generierten) Unit-Tests sind auf Anhieb durchgelaufen
- Tests decken ab: API-Endpunkte, Warenkorb-Berechnungslogik, Datenbankzugriff und Frontend-Struktur
- Die Frontend-Tests (`test_frontend_components.py`, `test_responsive_design.py`) prüfen rein syntaktisch, ob bestimmte Zeichenketten und HTML-Strukturen im Quellcode vorhanden sind – sie testen kein reales Browserverhalten; echte E2E-Tests fehlen
- Beim Testlauf werden 16 Deprecation-Warnungen ausgegeben (veraltetes `@app.on_event` und `datetime.utcnow()`)

### Testabdeckung
- Backend-Testabdeckung (Statement + Branch): **96%** gesamt
- Alle API-Module (`cart.py`, `orders.py`, `products.py`, `reviews.py`, `models.py`, `schemas.py`) mit 100% abgedeckt
- Schwächere Abdeckung bei `database.py` (65%) und `seed.py` (79%), da Fehler- und Fallback-Pfade nicht getestet werden

```
Name                          Stmts   Miss Branch BrPart  Cover
---------------------------------------------------------------
backend\app\api\cart.py          78      0     18      0   100%
backend\app\api\orders.py        39      0     12      0   100%
backend\app\api\products.py      16      0      2      0   100%
backend\app\api\reviews.py       31      0      2      0   100%
backend\app\database.py          17      6      0      0    65%
backend\app\main.py              23      3      2      1    84%
backend\app\models.py            64      0      0      0   100%
backend\app\schemas.py           53      0      0      0   100%
backend\app\seed.py              23      5      6      1    79%
---------------------------------------------------------------
TOTAL                           344     14     42      2    96%
```

### Lesbarkeit und Wartbarkeit
#### Backend
- Der Code ist gut lesbar und übersichtlich durch die konsequente Aufteilung in Module
- Funktionen und Klassen sind verständlich benannt
- Docstrings in `main.py` und den Modellen vorhanden, was die Orientierung erleichtert
- Die In-Memory-Implementierung des Warenkorbs ist zwar lesbar, aber architektonisch fragwürdig – ein Refactoring auf Datenbankpersistenz wäre notwendig für den Produktionseinsatz
- Verwendung von `@app.on_event` und `datetime.utcnow()` erfordert Anpassungen für Zukunftssicherheit

#### Frontend
- Das Frontend ist gut strukturiert und lesbar; eine Component pro Seite/Bereich
- Gemeinsam genutzte Logik ist in `api.js` zentralisiert
- Tailwind-Standard-Klassen sind gut verständlich, da kein Custom-Theme das Lesen erschwert

### Effizienz
#### Verbrauch Token: 
- Input-Token: ca. 8,7 Millionen
- Output-Token: ca. 400.000
- Requests: ca. 300 Api-Requests
- Arbeitszeit: ca. 50 Minuten

### Kosten
- Gesamtkosten: 11.25 $


## Single-Agent System

### Codequalität
#### Backend:
- Der Code ist ebenfalls sehr modular aufgebaut ("Separation of Concerns") – mit eigenen Dateien für `main.py`, `database.py`, `models.py`, `schemas.py`, `schemas.py`, `seed.py` und `session.py`
- Die API-Endpunkte wurden thematisch in ein eigenes Unterverzeichnis `/app/api` unterteilt (cart, orders, products, reviews)
- Es wird das moderne FastAPI Lifecycle-Management (`@asynccontextmanager lifespan`) verwendet – **kein deprecated `@app.on_event`** im Gegensatz zum Multi-Agent-System
- Umfassendes und sicherheitsbewusstes Fehlerhandling: eigene Exception-Handler für Validierungsfehler, HTTP-Exceptions und ungefangene Ausnahmen; Fehlermeldungen nach außen sind absichtlich generisch gehalten (keine internen Details werden geleakt)
- API-Dokumentationsrouten (`/docs`, `/redoc`, `/openapi.json`) sind explizit deaktiviert (Security by default)
- CORS ist restriktiv auf localhost konfiguriert
- Datenbankmodelle mit sorgfältigen Constraints und `nullable`-Attributen (SQLAlchemy `Mapped`-Annotationen)
- Keine IDE-Warnungen bezüglich veralteter Funktionsaufrufe feststellbar

#### Frontend
- Das Frontend wurde in gut benannte Web Components aufgeteilt: `product-list`, `product-detail`, `shopping-cart`, `checkout-page`, `order-confirmation`, `legal`-Pages, `site-header`, `site-footer`
- Gemeinsame Hilfsfunktionen (API-Calls, Fehlerformatierung, Skeleton-Loader, Sternebewertung) wurden in `api.js` ausgelagert – analog zum Multi-Agent-System, jedoch konsistenter angewandt
- Debounced Search-Input verhindert unnötige API-Calls beim Tippen
- Fehlerbehandlung in allen asynchronen Funktionen vorhanden

### Produktqualität
- Der Output hat auf Anhieb kompiliert und gestartet
- Das Design ist modern und stimmig (eigenes Branding „SneakerHaus", benutzerdefiniertes Tailwind-Theme mit Farben `ink`, `clay`, `sand`, `sage`)
- Produktübersicht mit Markenfilter, Suche und Sortierung funktioniert
- Produktdetailseite mit Größenauswahl, Bewertungen und Mengenstepper funktioniert
- Warenkorb (Hinzufügen, Aktualisieren, Löschen) funktioniert
- Bestellabschluss mit Lieferadresse und Zahlungsauswahl funktioniert
- Bestellbestätigungsseite mit Positionen und Gesamtsumme funktioniert
- Impressum, AGB/Widerruf und Kontaktseite vorhanden
- Inputvalidierung beim Checkout findet serverseitig statt (z.B. ungültige E-Mail → 400-Fehler); im Gegensatz zum Multi-Agent-System wurde hier Validierung konsequent umgesetzt

### Funktionale Korrektheit (bestehende Unit Tests)
- Alle 21 (von der KI generierten) Unit-Tests sind auf Anhieb durchgelaufen
- Tests decken ab: API-Vertragskonformität, Warenkorb- und Bestelllogik, Produkt- und Bewertungsendpunkte sowie Frontend-Strukturtests
- Im Vergleich zum Multi-Agent-System weniger Tests in absoluter Zahl (21 vs. 72), jedoch qualitativ hochwertiger: Tests prüfen echtes API-Verhalten (Status-Codes, Response-Body-Struktur, Geschäftslogik) anstatt rein syntaktisch nach Code-Fragmenten zu suchen
- Die Frontend-Tests (`test_frontend_contract.py`) sind strukturell ähnlich wie beim Multi-Agent-System – sie prüfen, ob bestimmte Web-Component-Definitionen und Routing-Einträge im Code vorhanden sind; echte E2E-Tests fehlen auch hier

### Testabdeckung
- Backend-Testabdeckung (Statement + Branch): **99%** gesamt (14 Dateien)
- 11 Dateien mit vollständiger 100%-Abdeckung; nur 3 Dateien darunter: `cart.py` (96%), `database.py` (95%) und `seed.py` (88%)

```
Name                          Stmts   Miss Branch BrPart  Cover
---------------------------------------------------------------
backend\__init__.py               0      0      0      0   100%
backend\app\__init__.py           0      0      0      0   100%
backend\app\api\__init__.py       0      0      0      0   100%
backend\app\api\cart.py          45      1     10      1    96%
backend\app\api\deps.py          22      0      4      0   100%
backend\app\api\orders.py        31      0      6      0   100%
backend\app\api\products.py      22      0      6      0   100%
backend\app\api\reviews.py       34      0      4      0   100%
backend\app\database.py          20      0      2      1    95%
backend\app\main.py              41      0      0      0   100%
backend\app\models.py            69      0      0      0   100%
backend\app\schemas.py           32      0      0      0   100%
backend\app\seed.py              15      1      2      1    88%
backend\app\session.py            9      0      2      0   100%
---------------------------------------------------------------
TOTAL                           340      2     36      3    99%
```

### Lesbarkeit und Wartbarkeit
#### Backend
- Sehr lesbar und gut strukturiert durch konsequente Kapselung
- Funktionen, Klassen und Module sind klar und verständlich benannt
- Verwendung moderner Python-Typisierung (`Mapped`-Annotationen in SQLAlchemy) macht den Code ausdrucksstark
- Zentrale Fehlerbehandlung in `main.py` hält die API-Module übersichtlich

#### Frontend
- Gleichwertig gut lesbar wie das Backend
- Jede Route/Seite hat eine eigene Component-Datei
- Gemeinsam genutzte Logik ist konsequent in `api.js` ausgelagert
- Tailwind-Klassen direkt im Template-String machen das Layout nachvollziehbar, erfordern jedoch Tailwind-Kenntnisse zum Lesen

### Effizienz
#### Verbrauch Token: 
- Input-Token: ca. 2,9 Millionen
- Output-Token: ca. 40.000
- Requests: ca. 50
- Arbeitszeit: ca. 10 Minuten

### Kosten
- Gesamtkosten: 2.44 $

---

## Fazit

Beide Systeme haben die gestellte Aufgabe grundsätzlich erfüllt: Der generierte Code kompilierte jeweils auf Anhieb, alle Features waren funktionsfähig und die generierten Tests liefen vollständig durch.

In der **Codequalität** zeigt das Single-Agent-System klare Vorteile: Es verwendet moderne FastAPI-Patterns (`lifespan`), ein einheitliches und sicherheitsbewusstes Fehlerformat, deaktivierte API-Dokumentationsrouten und persistente Datenbankpersistenz für den Warenkorb. Das Multi-Agent-System weist dagegen mehrere technische Schwächen auf – darunter veraltete API-Aufrufe, einen flüchtigen In-Memory-Warenkorb und fehlende Eingabevalidierung beim Checkout.

Bei der **Testabdeckung** schneidet das Single-Agent-System mit 99% (Statement + Branch) gegenüber 96% beim Multi-Agent-System besser ab. Noch bedeutender ist die **Testqualität**: Die 21 Tests des Single-Agent-Systems prüfen echtes API-Verhalten inklusive Fehlerformate und Geschäftslogik, während ein Großteil der 72 Multi-Agent-Tests lediglich das Vorhandensein von Code-Fragmenten im Quelltext prüft.

Das **Produkt** des Single-Agent-Systems wirkt ausgereifter – mit durchdachtem Branding, einem kohärenten Design-System und konsequenter Fehlerbehandlung auf allen Ebenen.

Auf der anderen Seite ist das Multi-Agent-System mit ~50 Minuten Laufzeit und 11,25 $ deutlich ressourcenintensiver als das Single-Agent-System (~10 Minuten, 2,44 $), ohne dass dieser Mehraufwand in einem qualitativ besseren Ergebnis resultiert. Insgesamt lieferte das Single-Agent-System in diesem Vergleich das qualitativ überzeugendere Ergebnis.