from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("LLM_ENABLED", "false")
    from app.config import get_settings

    get_settings.cache_clear()
    import app.database as database

    database.engine.dispose()
    database.engine = database.build_engine()
    database.SessionLocal.configure(bind=database.engine)
    database.init_db()
    yield
    database.engine.dispose()
