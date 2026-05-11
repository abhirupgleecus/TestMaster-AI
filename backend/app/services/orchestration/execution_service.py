import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.test_execution import (
    TestExecutionStatus,
)
from app.repositories import (
    GenerationSessionRepository,
    TestExecutionRepository,
    TestReportRepository,
    TestScriptRepository,
)
from app.services.playwright_service import (
    PlaywrightService,
)
from app.services.report_service import (
    ReportService,
)


class ExecutionService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.playwright_service = (
            PlaywrightService()
        )

        self.report_service = ReportService()

        self.generation_session_repository = (
            GenerationSessionRepository(
                session,
            )
        )

        self.test_script_repository = (
            TestScriptRepository(
                session,
            )
        )

        self.test_execution_repository = (
            TestExecutionRepository(
                session,
            )
        )

        self.test_report_repository = (
            TestReportRepository(
                session,
            )
        )

    async def execute_session_script(
        self,
        session_id: uuid.UUID,
    ):
        generation_session = (
            await self
            .generation_session_repository
            .get_session_by_id(
                session_id,
            )
        )

        if generation_session is None:
            raise ValueError(
                "Generation session not found."
            )

        test_script = (
            await self
            .test_script_repository
            .get_script_by_session_id(
                session_id,
            )
        )

        if test_script is None:
            raise ValueError(
                "Generated script not found."
            )

        execution = (
            await self
            .test_execution_repository
            .create_execution(
                script_id=test_script.id,
            )
        )

        await (
            self
            .test_execution_repository
            .update_execution_status(
                execution.id,
                TestExecutionStatus.RUNNING,
            )
        )

        self.playwright_service.write_script_file(
            session_id=session_id,
            script_content=(
                test_script.script_content
            ),
        )

        execution_result = (
            await self.playwright_service
            .execute_script(
                session_id=session_id,
                execution_id=execution.id,
            )
        )

        final_status = (
            TestExecutionStatus.COMPLETED
            if execution_result.success
            else TestExecutionStatus.FAILED
        )

        completed_execution = (
            await self
            .test_execution_repository
            .complete_execution(
                execution_id=execution.id,

                playwright_json=(
                    execution_result
                    .playwright_json
                ),

                playwright_html_path=(
                    execution_result
                    .html_report_path
                ),

                total_tests=(
                    execution_result
                    .total_tests
                ),

                passed_tests=(
                    execution_result
                    .passed_tests
                ),

                failed_tests=(
                    execution_result
                    .failed_tests
                ),

                skipped_tests=(
                    execution_result
                    .skipped_tests
                ),

                duration_ms=(
                    execution_result
                    .duration_ms
                ),

                error_log=(
                    execution_result.stderr
                ),

                stdout=(
                    execution_result.stdout
                ),

                status=final_status,
            )
        )

        if completed_execution is None:
            raise ValueError(
                "Execution completion failed."
            )

        generated_report = (
            await self.report_service
            .generate_report(
                completed_execution,
            )
        )

        await (
            self
            .test_report_repository
            .create_or_update_report(
                execution_id=(
                    generated_report["execution_id"]
                ),

                executive_summary=(
                    generated_report["executive_summary"]
                ),

                detailed_analysis=(
                    generated_report["detailed_analysis"]
                ),

                overall_status=(
                    generated_report["overall_status"]
                ),

                confidence_score=(
                    generated_report["confidence_score"]
                ),
            )
        )

        return completed_execution