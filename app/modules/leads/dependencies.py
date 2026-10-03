from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.modules.leads.repository import LeadRepository
from app.modules.leads.service import LeadService
from app.modules.tags.dependencies import build_tag_service


def build_lead_service(session: AsyncSession) -> LeadService:
    return LeadService(LeadRepository(session), build_tag_service(session))


def get_lead_service(session: Annotated[AsyncSession, Depends(get_session)]) -> LeadService:
    return build_lead_service(session)


LeadServiceDep = Annotated[LeadService, Depends(get_lead_service)]
