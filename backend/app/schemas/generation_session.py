import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.generation_session import GenerationSessionStatus


class GenerationSessionCreate(BaseModel):
    context_input: str = Field(
        min_length=1,
    )


class GenerationSessionResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    context_input: str
    status: GenerationSessionStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)