from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.leads.models import LeadSource, LeadStatus
from app.modules.tags.schemas import TagRead


class LeadBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    contact: str | None = Field(default=None, max_length=255)
    request: str | None = None


class LeadCreate(LeadBase):
    status: LeadStatus = LeadStatus.NEW
    tag_ids: list[int] = Field(default_factory=list)


class LeadUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    contact: str | None = Field(default=None, max_length=255)
    request: str | None = None
    status: LeadStatus | None = None

    def changes(self) -> dict[str, object]:
        values = self.model_dump(exclude_unset=True)
        return {k: v for k, v in values.items() if not (k in _NOT_NULLABLE and v is None)}


_NOT_NULLABLE = frozenset({"name", "status"})


class LeadFilter(BaseModel):
    tag_id: int | None = None
    source: LeadSource | None = None
    status: LeadStatus | None = None
    q: str | None = Field(default=None, description="Поиск по имени, контакту и запросу")


class TelegramSender(BaseModel):
    chat_id: int
    full_name: str
    username: str | None = None

    @property
    def contact(self) -> str:
        return f"@{self.username}" if self.username else f"tg://user?id={self.chat_id}"


class BotApplication(LeadBase):
    sender: TelegramSender
    service: str | None = None


class LeadMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    created_at: datetime


class LeadRead(LeadBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: LeadSource
    status: LeadStatus
    telegram_username: str | None
    created_at: datetime
    updated_at: datetime
    tags: list[TagRead]


class LeadDetail(LeadRead):
    messages: list[LeadMessageRead]
