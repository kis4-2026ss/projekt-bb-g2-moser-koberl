# [Developer iter=1] Routing und Navigation

exit_code: 0

---

Die Frontend-Web-Components und Frontend-Tests sind im Arbeitsverzeichnis bereits vollständig vorhanden; ich habe keine unnötigen Änderungen vorgenommen.

Verifiziert:
- Alle erwarteten Custom Elements werden registriert: `registered 10`
- API-/Routing-Helper laufen im Node-Smoke-Test: `api helpers ok`
- Keine offensichtlichen Platzhalter wie `TODO`, `FIXME`, `NotImplemented` in Frontend/Backend

Nicht vollständig ausführbar:
- `pytest -q` und `python -m pytest -q` konnten nicht laufen, weil `pytest` in der Umgebung fehlt.
- `python -m pip install -r requirements-dev.txt` scheiterte, da der Paketindex keine Versionen liefert: `No matching distribution found for pytest>=8.0.0`.

Die vorhandenen Frontend-Tests liegen in `tests/test_frontend_components.py` und decken Registrierung, Routing, API-Verträge, Form-Verhalten und Node-Smoke-Importe ab.

