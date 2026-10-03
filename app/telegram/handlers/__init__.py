from aiogram import Router

from app.telegram.handlers import application, business


def build_router() -> Router:
    router = Router(name="root")
    router.include_routers(business.create_router(), application.create_router())
    return router
