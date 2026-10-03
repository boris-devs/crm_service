from collections.abc import Sequence

from sqlalchemy import func, select

from app.core.repository import SQLAlchemyRepository
from app.modules.tags.models import Tag, lead_tags


class TagRepository(SQLAlchemyRepository[Tag]):
    model = Tag

    async def list_with_counts(self) -> Sequence[tuple[Tag, int]]:
        stmt = (
            select(Tag, func.count(lead_tags.c.lead_id))
            .outerjoin(lead_tags, lead_tags.c.tag_id == Tag.id)
            .group_by(Tag.id)
            .order_by(Tag.name)
        )
        return (await self.session.execute(stmt)).all()

    async def get_by_name(self, name: str) -> Tag | None:
        stmt = select(Tag).where(func.lower(Tag.name) == name.lower())
        return await self.session.scalar(stmt)

    async def get_many(self, tag_ids: Sequence[int]) -> Sequence[Tag]:
        if not tag_ids:
            return []
        return (await self.session.scalars(select(Tag).where(Tag.id.in_(tag_ids)))).all()
