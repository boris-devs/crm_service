from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import Settings, get_settings
from app.core.exceptions import register_exception_handlers
from app.core.security import require_admin
from app.modules.leads.router import router as leads_router
from app.modules.tags.router import router as tags_router
from app.telegram.webhook import create_webhook

STATIC_DIR = Path(__file__).parent / "web" / "static"
OPENAPI_URL = "/openapi.json"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    webhook = create_webhook(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if webhook is None:
            yield
            return
        await webhook.register(settings.webhook_base_url)
        try:
            yield
        finally:
            await webhook.close()

    app = FastAPI(
        title="Mini CRM", version="0.1.0", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None
    )
    register_exception_handlers(app)

    api = APIRouter(prefix="/api", dependencies=[Depends(require_admin)])
    api.include_router(leads_router)
    api.include_router(tags_router)
    app.include_router(api)

    protected = APIRouter(include_in_schema=False, dependencies=[Depends(require_admin)])

    @protected.get("/")
    async def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @protected.get(OPENAPI_URL)
    async def openapi() -> dict:
        return app.openapi()

    @protected.get("/docs")
    async def docs() -> HTMLResponse:
        return get_swagger_ui_html(openapi_url=OPENAPI_URL, title=f"{app.title} — API")

    app.include_router(protected)

    if webhook is not None:
        app.include_router(webhook.build_router())

    @app.get("/health", include_in_schema=False)
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app


app = create_app()
