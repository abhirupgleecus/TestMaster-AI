import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.test_report import TestReportStatus


class TestReportResponse(BaseModel):
    id: uuid.UUID
    execution_id: uuid.UUID

    executive_summary: str

    overall_status: TestReportStatus

    confidence_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TestReportDetailResponse(TestReportResponse):
    detailed_analysis: dict