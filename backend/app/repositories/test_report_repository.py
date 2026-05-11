import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.test_report import (
    TestReport,
    TestReportStatus,
)


class TestReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_or_update_report(
        self,
        execution_id: uuid.UUID,
        executive_summary: str,
        detailed_analysis: dict,
        overall_status: TestReportStatus,
        confidence_score: float | None,
    ) -> TestReport:
        existing_report = await self.get_report_by_execution_id(
            execution_id,
        )

        if existing_report is not None:
            existing_report.executive_summary = (
                executive_summary
            )

            existing_report.detailed_analysis = (
                detailed_analysis
            )

            existing_report.overall_status = (
                overall_status
            )

            existing_report.confidence_score = (
                confidence_score
            )

            await self.session.commit()
            await self.session.refresh(existing_report)

            return existing_report

        test_report = TestReport(
            execution_id=execution_id,
            executive_summary=executive_summary,
            detailed_analysis=detailed_analysis,
            overall_status=overall_status,
            confidence_score=confidence_score,
        )

        self.session.add(test_report)

        await self.session.commit()
        await self.session.refresh(test_report)

        return test_report

    async def get_report_by_id(
        self,
        report_id: uuid.UUID,
    ) -> TestReport | None:
        statement = select(TestReport).where(
            TestReport.id == report_id,
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_report_by_execution_id(
        self,
        execution_id: uuid.UUID,
    ) -> TestReport | None:
        statement = select(TestReport).where(
            TestReport.execution_id == execution_id,
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()