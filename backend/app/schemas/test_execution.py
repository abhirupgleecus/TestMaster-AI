import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.test_execution import TestExecutionStatus


class TestExecutionResponse(BaseModel):
    id: uuid.UUID
    script_id: uuid.UUID

    status: TestExecutionStatus

    playwright_html_path: str | None

    total_tests: int | None
    passed_tests: int | None
    failed_tests: int | None
    skipped_tests: int | None

    duration_ms: int | None

    error_log: str | None

    started_at: datetime
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class TestExecutionDetailResponse(TestExecutionResponse):
    playwright_json: dict | None