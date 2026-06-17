import importlib
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import close_all_sessions

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture()
def client(monkeypatch):
    test_data_dir = Path.cwd() / ".test-data"
    test_data_dir.mkdir(exist_ok=True)
    db_path = test_data_dir / f"shop_test_{uuid4().hex}.db"
    monkeypatch.setenv("SNEAKERHAUS_DATABASE_URL", f"sqlite:///{db_path.as_posix()}")

    for module_name in list(sys.modules):
        if module_name == "backend.app" or module_name.startswith("backend.app."):
            del sys.modules[module_name]

    app_module = importlib.import_module("backend.app.main")
    with TestClient(app_module.app) as test_client:
        yield test_client
    close_all_sessions()
    app_module.init_db.__globals__["engine"].dispose()
    if db_path.exists():
        db_path.unlink()
