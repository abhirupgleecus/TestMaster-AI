import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.test_report_repository import TestReportRepository
from app.schemas.test_report import TestReportDetailResponse

router = APIRouter()

def get_test_report_repo(db: AsyncSession = Depends(get_db)) -> TestReportRepository:
    return TestReportRepository(db)

@router.get("/executions/{execution_id}/report", response_model=TestReportDetailResponse)
async def get_report(
    execution_id: uuid.UUID,
    report_repo: TestReportRepository = Depends(get_test_report_repo),
):
    report = await report_repo.get_report_by_execution_id(execution_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
