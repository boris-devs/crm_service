from collections.abc import Sequence

from app.core.exceptions import ConflictError, NotFoundError
from app.modules.tags.models import Tag
from app.modules.tags.repository import TagRepository
from app.modules.tags.schemas import TagCreate, TagWithCount


class TagService:
    def __init__(self, tags: TagRepository) -> None:
        self._tags = tags

    async def list_all(self) -> list[TagWithCount]:
        rows = await self._tags.list_with_counts()
        return [
            TagWithCount(id=tag.id, name=tag.name, color=tag.color, lead_count=count) for tag, count in rows
        ]

    async def get(self, tag_id: int) -> Tag:
        tag = await self._tags.get(tag_id)
        if tag is None:
            raise NotFoundError(f"Тег {tag_id} не найден")
        return tag

    async def get_many(self, tag_ids: Sequence[int]) -> list[Tag]:
        unique_ids = set(tag_ids)
        tags = list(await self._tags.get_many(list(unique_ids)))
        if len(tags) != len(unique_ids):
            missing = unique_ids - {tag.id for tag in tags}
            raise NotFoundError(f"Теги не найдены: {sorted(missing)}")
        return tags

    async def create(self, data: TagCreate) -> Tag:
        name = data.name.strip()
        if await self._tags.get_by_name(name):
            raise ConflictError(f"Тег «{name}» уже существует")
        return await self._tags.add(Tag(name=name, color=data.color))

    async def get_or_create(self, name: str) -> Tag:
        name = name.strip()
        return await self._tags.get_by_name(name) or await self._tags.add(Tag(name=name))

    async def delete(self, tag_id: int) -> None:
        await self._tags.delete(await self.get(tag_id))
