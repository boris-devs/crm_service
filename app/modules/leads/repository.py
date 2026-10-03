from collections.abc import Sequence

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import selectinload

from app.core.repository import SQLAlchemyRepository
from app.modules.leads.models import Lead, LeadMessage, LeadSource
from app.modules.leads.schemas import LeadFilter
from app.modules.tags.models import Tag


class LeadRepository(SQLAlchemyRepository[Lead]):
    model = Lead

    async def list_all(self, filters: LeadFilter) -> Sequence[Lead]:
        stmt = self._apply_filters(select(Lead), filters).order_by(Lead.created_at.desc(), Lead.id.desc())
        return (await self.session.scalars(stmt)).all()

    async def get_with_messages(self, lead_id: int) -> Lead | None:
        stmt = select(Lead).where(Lead.id == lead_id).options(selectinload(Lead.messages))
        return await self.session.scalar(stmt)

    async def add_message(self, lead: Lead, text: str) -> LeadMessage:
        message = LeadMessage(lead_id=lead.id, text=text)
        self.session.add(message)
        await self.session.flush()
        return message

    async def find_by_telegram_chat(self, source: LeadSource, chat_id: int) -> Lead | None:
        stmt = (
            select(Lead)
            .where(Lead.source == source, Lead.telegram_chat_id == chat_id)
            .order_by(Lead.created_at.desc())
            .limit(1)
        )
        return await self.session.scalar(stmt)

    @staticmethod
    def _apply_filters(stmt: Select[tuple[Lead]], filters: LeadFilter) -> Select[tuple[Lead]]:
        if filters.tag_id is not None:
            stmt = stmt.where(Lead.tags.any(Tag.id == filters.tag_id))
        if filters.source is not None:
            stmt = stmt.where(Lead.source == filters.source)
        if filters.status is not None:
            stmt = stmt.where(Lead.status == filters.status)
        if filters.q and (query := filters.q.strip()):
            pattern = f"%{query}%"
            stmt = stmt.where(
                or_(Lead.name.ilike(pattern), Lead.contact.ilike(pattern), Lead.request.ilike(pattern))
            )
        return stmt
