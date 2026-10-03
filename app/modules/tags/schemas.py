from pydantic import BaseModel, ConfigDict, Field

from app.modules.tags.models import DEFAULT_TAG_COLOR


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    color: str = Field(default=DEFAULT_TAG_COLOR, pattern=r"^#[0-9a-fA-F]{6}$")


class TagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    color: str


class TagWithCount(TagRead):
    lead_count: int
