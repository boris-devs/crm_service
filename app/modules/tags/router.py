from fastapi import APIRouter, status

from app.modules.tags.dependencies import TagServiceDep
from app.modules.tags.schemas import TagCreate, TagRead, TagWithCount

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagWithCount])
async def list_tags(service: TagServiceDep) -> list[TagWithCount]:
    return await service.list_all()


@router.post("", response_model=TagRead, status_code=status.HTTP_201_CREATED)
async def create_tag(data: TagCreate, service: TagServiceDep):
    return await service.create(data)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(tag_id: int, service: TagServiceDep) -> None:
    await service.delete(tag_id)
