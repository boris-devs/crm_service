from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.config import get_settings


class Base(DeclarativeBase):
	pass


def utcnow() -> datetime:
	return datetime.now(UTC)


class TimestampMixin:
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), default=utcnow, server_default=func.now()
	)
	updated_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), default=utcnow, onupdate=utcnow, server_default=func.now()
	)


engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
session_factory = async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def session_scope(factory: async_sessionmaker[AsyncSession] = session_factory) -> AsyncIterator[AsyncSession]:
	async with factory() as session:
		try:
			yield session
			await session.commit()
		except Exception:
			await session.rollback()
			raise


async def get_session() -> AsyncIterator[AsyncSession]:
	async with session_scope() as session:
		yield session
