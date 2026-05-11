from pydantic import BaseModel, Field

from app.models.test_report import (
    TestReportStatus,
)
from app.schemas.test_case import (
    TestCaseCreate,
)


class TestCaseGenerationResponse(BaseModel):
    test_cases: list[TestCaseCreate]


class DetailedAnalysis(BaseModel):
    highlights: list[str] = Field(
        default_factory=list,
    )

    failures: list[str] = Field(
        default_factory=list,
    )

    recommendations: list[str] = Field(
        default_factory=list,
    )


class TestReportGenerationResponse(BaseModel):
    executive_summary: str

    detailed_analysis: DetailedAnalysis

    overall_status: TestReportStatus

    confidence_score: float | None = None