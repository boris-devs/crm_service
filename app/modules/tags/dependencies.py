from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.modules.tags.repository import TagRepository
from app.modules.tags.service import TagService


def build_tag_service(session: AsyncSession) -> TagService:
    return TagService(TagRepository(session))


def get_tag_service(session: Annotated[AsyncSession, Depends(get_session)]) -> TagService:
    return build_tag_service(session)


TagServiceDep = Annotated[TagService, Depends(get_tag_service)]
