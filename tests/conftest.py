import os
import tempfile
from collections.abc import AsyncIterator
from pathlib import Path

_DB_FILE = Path(tempfile.gettempdir()) / "crm_service_tests.sqlite3"
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{_DB_FILE.as_posix()}")
os.environ["ADMIN_PASSWORD"] = ""
os.environ["BOT_MODE"] = "polling"

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event

from app.core.db import Base, engine
from app.main import app
from app.modules import models

if engine.dialect.name == "sqlite":
    @event.listens_for(engine.sync_engine, "connect")
    def _enable_sqlite_fk(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")


@pytest.fixture(autouse=True)
async def clean_db() -> AsyncIterator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        yield http

