from datetime import datetime
from enum import StrEnum

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, TimestampMixin, utcnow
from app.modules.tags.models import Tag, lead_tags


class LeadSource(StrEnum):
    TELEGRAM_BOT = "telegram_bot"
    TELEGRAM_ACCOUNT = "telegram_account"
    MANUAL = "manual"


class LeadStatus(StrEnum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    WON = "won"
    LOST = "lost"


def _str_enum(enum_cls: type[StrEnum]) -> Enum:
    return Enum(enum_cls, native_enum=False, length=32, values_callable=lambda e: [m.value for m in e])


class Lead(TimestampMixin, Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    contact: Mapped[str | None] = mapped_column(String(255))
    request: Mapped[str | None] = mapped_column(Text)
    source: Mapped[LeadSource] = mapped_column(_str_enum(LeadSource), index=True)
    status: Mapped[LeadStatus] = mapped_column(
        _str_enum(LeadStatus), default=LeadStatus.NEW, server_default=LeadStatus.NEW.value, index=True
    )
    telegram_chat_id: Mapped[int | None] = mapped_column(BigInteger, index=True)
    telegram_username: Mapped[str | None] = mapped_column(String(64))

    tags: Mapped[list[Tag]] = relationship(secondary=lead_tags, lazy="selectin", order_by=Tag.name)
    messages: Mapped[list["LeadMessage"]] = relationship(
        back_populates="lead",
        lazy="raise",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="LeadMessage.created_at",
    )


class LeadMessage(Base):
    __tablename__ = "lead_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    lead: Mapped[Lead] = relationship(back_populates="messages", lazy="raise")
