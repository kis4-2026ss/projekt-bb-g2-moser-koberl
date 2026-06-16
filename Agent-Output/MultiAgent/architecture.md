## Komponenten-Übersicht
- **Backend**: FastAPI-Anwendung, die statische Dateien serviert und REST-APIs bereitstellt.
- **Frontend**: Web Components, die mit Vanilla JavaScript und Tailwind CSS erstellt wurden.

## Datenmodell
### Tabellen und Felder
1. **Sneaker**
   - id (Integer, Primary Key)
   - name (String)
   - brand (String)
   - price (Decimal)
   - currency (String, default='EUR')
   - short_description (String)
   - long_description (String)
   - image_url (String)
   - sizes (JSON Array)
   - color (String)
   - material (String)
   - stock (Integer)
   - rating (Float)
   - is_new (Boolean)

2. **Review**
   - id (Integer, Primary Key)
   - product_id (Integer, Foreign Key)
   - author (String, nullable)
   - rating (Integer)
   - comment (String)
   - created_at (DateTime)

3. **Order**
   - id (Integer, Primary Key)
   - created_at (DateTime)
   - status (String)
   - shipping_name (String)
   - shipping_street (String)
   - shipping_zip (String)
   - shipping_city (String)
   - shipping_country (String)
   - email (String)
   - payment_method (String)
   - subtotal (Decimal)
   - total (Decimal)

4. **OrderItem**
   - id (Integer, Primary Key)
   - order_id (Integer, Foreign Key)
   - product_id (Integer, Foreign Key)
   - name_snapshot (String)
   - brand_snapshot (String)
   - price_snapshot (Decimal)
   - image_url_snapshot (String)
   - size (String)
   - quantity (Integer)
   - line_total (Decimal)

## API-Endpunkte
1. **Produkte**
   - `GET /api/products`  
     - **Response**: List von Sneaker-Objekten
   - `GET /api/products/{id}`  
     - **Response**: Sneaker-Objekt oder 404

2. **Warenkorb**
   - `GET /api/cart`  
     - **Response**: Cart-Objekt
   - `POST /api/cart/items`  
     - **Payload**: `{product_id, size, quantity}`  
     - **Response**: 201 bei Erfolg
   - `PATCH /api/cart/items/{item_id}`  
     - **Payload**: `{quantity}`  
     - **Response**: 204 bei Erfolg
   - `DELETE /api/cart/items/{item_id}`  
     - **Response**: 204 bei Erfolg

3. **Bestellungen**
   - `POST /api/orders`  
     - **Payload**: `{shipping, payment_method}`  
     - **Response**: 201 mit Bestellinformationen
   - `GET /api/orders/{id}`  
     - **Response**: Order-Objekt oder 404

4. **Bewertungen**
   - `GET /api/products/{id}/reviews`  
     - **Response**: Durchschnittsbewertung und Liste der Reviews
   - `POST /api/products/{id}/reviews`  
     - **Payload**: `{author, rating, comment}`  
     - **Response**: 201 bei Erfolg

## Web-Component-Liste
- `<product-list>`
- `<product-detail>`
- `<shopping-cart>`
- `<checkout-page>`
- `<order-confirmation>`
- `<imprint-page>`
- `<terms-page>`
- `<contact-page>`
- `<not-found>`

## Dateilayout
```
./backend/app/main.py             (FastAPI app, mounted StaticFiles)
./backend/app/database.py         (SQLAlchemy Engine + SessionLocal + init_db)
./backend/app/models.py           (ORM Models)
./backend/app/schemas.py          (Pydantic Schemas)
./backend/app/api/                (Router: products, cart, orders, reviews)
./backend/app/seed.py             (Seed-Daten)
./frontend/index.html
./frontend/components/*.js        (Web Components)
./frontend/styles/*.css           (optional, primaer Tailwind)
./tests/                          (pytest, vom Tester-Agent gefuellt)
./requirements.txt
./README.md
```

## Wichtige Tech-Entscheidungen
- Verwendung von SQLite für die Datenpersistenz.
- FastAPI für die Backend-Entwicklung aufgrund der hohen Performance und der einfachen Handhabung von REST-APIs.
- Web Components für das Frontend, um eine modulare und wiederverwendbare Struktur zu gewährleisten.