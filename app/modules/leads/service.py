from collections.abc import Iterable, Sequence

from app.core.db import utcnow
from app.core.exceptions import NotFoundError
from app.modules.leads.models import Lead, LeadMessage, LeadSource
from app.modules.leads.repository import LeadRepository
from app.modules.leads.schemas import BotApplication, LeadCreate, LeadFilter, LeadUpdate, TelegramSender
from app.modules.tags.models import Tag
from app.modules.tags.service import TagService


class LeadService:
    def __init__(self, leads: LeadRepository, tags: TagService) -> None:
        self._leads = leads
        self._tags = tags

    async def list_all(self, filters: LeadFilter) -> Sequence[Lead]:
        return await self._leads.list_all(filters)

    async def get(self, lead_id: int) -> Lead:
        return self._ensure_found(await self._leads.get(lead_id), lead_id)

    async def get_detail(self, lead_id: int) -> Lead:
        return self._ensure_found(await self._leads.get_with_messages(lead_id), lead_id)

    async def create_manual(self, data: LeadCreate) -> Lead:
        lead = Lead(
            name=data.name,
            contact=data.contact,
            request=data.request,
            status=data.status,
            source=LeadSource.MANUAL,
        )
        return await self._save_new(lead, await self._tags.get_many(data.tag_ids))

    async def create_from_bot(self, application: BotApplication) -> Lead:
        tags = [await self._tags.get_or_create(application.service)] if application.service else []
        lead = Lead(
            name=application.name,
            contact=application.contact or application.sender.contact,
            request=application.request,
            source=LeadSource.TELEGRAM_BOT,
            **self._telegram_fields(application.sender),
        )
        return await self._save_new(lead, tags)

    async def register_incoming_message(self, sender: TelegramSender, text: str) -> Lead:
        lead = await self._leads.find_by_telegram_chat(LeadSource.TELEGRAM_ACCOUNT, sender.chat_id)
        if lead is None:
            lead = Lead(
                name=sender.full_name,
                contact=sender.contact,
                request=text,
                source=LeadSource.TELEGRAM_ACCOUNT,
                **self._telegram_fields(sender),
            )
            return await self._save_new(lead, tags=[], messages=[LeadMessage(text=text)])

        await self._leads.add_message(lead, text)
        lead.updated_at = utcnow()
        await self._leads.flush()
        return lead

    async def update(self, lead_id: int, data: LeadUpdate) -> Lead:
        lead = await self.get(lead_id)
        for field, value in data.changes().items():
            setattr(lead, field, value)
        await self._leads.flush()
        return lead

    async def delete(self, lead_id: int) -> None:
        await self._leads.delete(await self.get(lead_id))

    async def add_tag(self, lead_id: int, tag_id: int) -> Lead:
        lead, tag = await self.get(lead_id), await self._tags.get(tag_id)
        if tag not in lead.tags:
            lead.tags.append(tag)
            await self._leads.flush()
        return lead

    async def remove_tag(self, lead_id: int, tag_id: int) -> Lead:
        lead = await self.get(lead_id)
        lead.tags = [tag for tag in lead.tags if tag.id != tag_id]
        await self._leads.flush()
        return lead

    async def _save_new(
        self, lead: Lead, tags: Iterable[Tag], messages: Iterable[LeadMessage] = ()
    ) -> Lead:
        lead.tags = list(tags)
        lead.messages = list(messages)
        return await self._leads.add(lead)

    @staticmethod
    def _telegram_fields(sender: TelegramSender) -> dict[str, object]:
        return {"telegram_chat_id": sender.chat_id, "telegram_username": sender.username}

    @staticmethod
    def _ensure_found(lead: Lead | None, lead_id: int) -> Lead:
        if lead is None:
            raise NotFoundError(f"Лид {lead_id} не найден")
        return lead
