import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=255,
    )

    target_url: str = Field(
        min_length=1,
        max_length=500,
    )

    description: str | None = None


class ProjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    target_url: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)