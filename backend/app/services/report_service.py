from app.models.test_execution import (
    TestExecution,
    TestExecutionStatus,
)
from app.models.test_report import (
    TestReportStatus,
)

from app.services.llm_service import (
    LLMService,
)


class ReportService:
    def __init__(self) -> None:
        self.llm_service = LLMService()

    def determine_report_status(
        self,
        execution: TestExecution,
    ) -> TestReportStatus:
        if execution.total_tests is None or execution.total_tests == 0:
            return TestReportStatus.FAILED

        if execution.failed_tests and execution.failed_tests > 0:
            return TestReportStatus.FAILED

        return TestReportStatus.PASSED

    def normalize_confidence_score(
        self,
        confidence_score: float | None,
    ) -> float:
        if confidence_score is None:
            return 0.5

        return max(
            0.0,
            min(confidence_score, 1.0),
        )

    async def generate_report(
        self,
        execution: TestExecution,
    ) -> dict:
        llm_response = (
            await self.llm_service
            .generate_test_report(
                execution,
            )
        )

        normalized_status = (
            self.determine_report_status(
                execution,
            )
        )

        normalized_confidence = (
            self.normalize_confidence_score(
                llm_response.confidence_score,
            )
        )

        overall_status = (
            normalized_status
        )

        executive_summary = llm_response.executive_summary
        if execution.total_tests is None or execution.total_tests == 0:
            executive_summary = (
                "CRITICAL: No tests were discovered or executed. "
                "This indicates a failure in test discovery or script generation. "
                f"Full Output: {execution.stdout}"
            )

        return {
            "execution_id": execution.id,

            "executive_summary": executive_summary,

            "detailed_analysis": (
                llm_response
                .detailed_analysis
                .model_dump()
            ),

            "overall_status": (
                overall_status
            ),

            "confidence_score": (
                normalized_confidence
            ),
        }