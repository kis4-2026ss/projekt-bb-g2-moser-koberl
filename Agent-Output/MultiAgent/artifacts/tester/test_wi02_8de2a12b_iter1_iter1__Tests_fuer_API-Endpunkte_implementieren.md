# [Tester iter=1] Tests fuer API-Endpunkte implementieren

exit_code: 0

---

Test-Suite erweitert, ohne produktiven Code zu ändern.

Geändert:
- [tests/test_api.py](C:/Users/sebas/Nextcloud/PC/Studium/KIS4/Projekt/Project-Output-Codex-MultiAgent/run_20260615T182618_0de67c86/code/tests/test_api.py:90): zusätzliche API-Tests für leeren Warenkorb, Kombinieren gleicher Cart-Items sowie Checkout-Fehler bei nachträglich entferntem Produkt bzw. entfernter Größe.
- [tests/test_database.py](C:/Users/sebas/Nextcloud/PC/Studium/KIS4/Projekt/Project-Output-Codex-MultiAgent/run_20260615T182618_0de67c86/code/tests/test_database.py:131): Review-CRUD-Roundtrip und OrderItem-Constraint `quantity > 0`.
- [tests/test_cart_logic.py](C:/Users/sebas/Nextcloud/PC/Studium/KIS4/Projekt/Project-Output-Codex-MultiAgent/run_20260615T182618_0de67c86/code/tests/test_cart_logic.py:51): direkte Logiktests für `clear_cart()` und getrennte Totals bei gleichem Produkt mit unterschiedlichen Größen.

Verifikation:
- `python -m py_compile tests\conftest.py tests\test_api.py tests\test_database.py tests\test_cart_logic.py tests\test_frontend_components.py` erfolgreich.
- `python -m pytest -q` konnte nicht laufen, weil `pytest` in der Umgebung nicht installiert ist. `requirements-dev.txt` enthält bereits `pytest>=8.0.0` und `httpx>=0.27.0`.

Angelegte/aktualisierte Testdateien:
- `tests/test_api.py`
- `tests/test_database.py`
- `tests/test_cart_logic.py`

