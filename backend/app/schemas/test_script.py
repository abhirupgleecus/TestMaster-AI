import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.test_script import TestScriptStatus


class TestScriptResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID

    file_path: str

    status: TestScriptStatus

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TestScriptDetailResponse(TestScriptResponse):
    script_content: str