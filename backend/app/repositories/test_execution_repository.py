import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.test_execution import (
    TestExecution,
    TestExecutionStatus,
)


class TestExecutionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_execution(
        self,
        script_id: uuid.UUID,
    ) -> TestExecution:
        test_execution = TestExecution(
            script_id=script_id,
            status=TestExecutionStatus.QUEUED,
        )

        self.session.add(test_execution)

        await self.session.commit()
        await self.session.refresh(test_execution)

        return test_execution

    async def get_execution_by_id(
        self,
        execution_id: uuid.UUID,
    ) -> TestExecution | None:
        statement = (
            select(TestExecution)
            .options(
                selectinload(TestExecution.test_report),
            )
            .where(TestExecution.id == execution_id)
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def update_execution_status(
        self,
        execution_id: uuid.UUID,
        status: TestExecutionStatus,
    ) -> TestExecution | None:
        test_execution = await self.get_execution_by_id(
            execution_id,
        )

        if test_execution is None:
            return None

        test_execution.status = status

        if status == TestExecutionStatus.RUNNING:
            test_execution.started_at = datetime.utcnow()

        if status in (
            TestExecutionStatus.COMPLETED,
            TestExecutionStatus.FAILED,
        ):
            test_execution.completed_at = (
                datetime.utcnow()
            )

        await self.session.commit()
        await self.session.refresh(test_execution)

        return test_execution

    async def complete_execution(
        self,
        execution_id: uuid.UUID,
        playwright_json: dict | None,
        playwright_html_path: str | None,
        total_tests: int | None,
        passed_tests: int | None,
        failed_tests: int | None,
        skipped_tests: int | None,
        duration_ms: int | None,
        error_log: str | None,
        stdout: str | None,
        status: TestExecutionStatus,
    ) -> TestExecution | None:
        test_execution = await self.get_execution_by_id(
            execution_id,
        )

        if test_execution is None:
            return None

        test_execution.playwright_json = playwright_json
        test_execution.playwright_html_path = (
            playwright_html_path
        )

        test_execution.total_tests = total_tests
        test_execution.passed_tests = passed_tests
        test_execution.failed_tests = failed_tests
        test_execution.skipped_tests = skipped_tests

        test_execution.duration_ms = duration_ms

        test_execution.error_log = error_log
        test_execution.stdout = stdout

        test_execution.status = status

        test_execution.completed_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(test_execution)

        return test_execution