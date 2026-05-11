import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.test_script_repository import TestScriptRepository
from app.repositories.test_execution_repository import TestExecutionRepository
from app.schemas.test_execution import TestExecutionResponse, TestExecutionDetailResponse
from app.services.orchestration.execution_service import ExecutionService

router = APIRouter()

def get_test_script_repo(db: AsyncSession = Depends(get_db)) -> TestScriptRepository:
    return TestScriptRepository(db)

def get_test_execution_repo(db: AsyncSession = Depends(get_db)) -> TestExecutionRepository:
    return TestExecutionRepository(db)

def get_execution_service(db: AsyncSession = Depends(get_db)) -> ExecutionService:
    return ExecutionService(db)

@router.post("/scripts/{script_id}/execute", response_model=TestExecutionDetailResponse)
async def execute_script(
    script_id: uuid.UUID,
    script_repo: TestScriptRepository = Depends(get_test_script_repo),
    execution_service: ExecutionService = Depends(get_execution_service),
):
    script = await script_repo.get_script_by_id(script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
        
    try:
        execution = await execution_service.execute_session_script(script.session_id)
        return execution
    except ValueError as e:
        print(f"Execution Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/executions/{execution_id}", response_model=TestExecutionDetailResponse)
async def get_execution(
    execution_id: uuid.UUID,
    execution_repo: TestExecutionRepository = Depends(get_test_execution_repo),
):
    execution = await execution_repo.get_execution_by_id(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution
