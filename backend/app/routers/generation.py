import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.generation_session_repository import GenerationSessionRepository
from app.repositories.test_case_repository import TestCaseRepository
from app.schemas.generation_session import GenerationSessionCreate, GenerationSessionResponse
from app.schemas.test_case import TestCaseResponse
from app.schemas.test_script import TestScriptResponse
from app.services.orchestration.generation_service import GenerationService

router = APIRouter()

def get_generation_session_repo(db: AsyncSession = Depends(get_db)) -> GenerationSessionRepository:
    return GenerationSessionRepository(db)

def get_test_case_repo(db: AsyncSession = Depends(get_db)) -> TestCaseRepository:
    return TestCaseRepository(db)

def get_generation_service(db: AsyncSession = Depends(get_db)) -> GenerationService:
    return GenerationService(db)

@router.post("/projects/{project_id}/sessions/", response_model=GenerationSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    project_id: uuid.UUID,
    session_data: GenerationSessionCreate,
    session_repo: GenerationSessionRepository = Depends(get_generation_session_repo),
    generation_service: GenerationService = Depends(get_generation_service),
):
    session = await session_repo.create_session(
        project_id=project_id,
        context_input=session_data.context_input,
    )
    
    # Trigger test case generation
    await generation_service.generate_test_cases_for_session(
        session_id=session.id,
        context_input=session_data.context_input,
    )
    
    return session

@router.get("/sessions/{session_id}/test-cases/", response_model=List[TestCaseResponse])
async def get_test_cases(
    session_id: uuid.UUID,
    test_case_repo: TestCaseRepository = Depends(get_test_case_repo),
):
    return await test_case_repo.get_test_cases_by_session_id(session_id)

class TestCaseSelectionUpdate(BaseModel):
    is_selected: bool

@router.patch("/sessions/{session_id}/test-cases/{test_case_id}", response_model=TestCaseResponse)
async def update_test_case_selection(
    session_id: uuid.UUID,
    test_case_id: uuid.UUID,
    update_data: TestCaseSelectionUpdate,
    test_case_repo: TestCaseRepository = Depends(get_test_case_repo),
):
    test_case = await test_case_repo.update_test_case_selection(
        test_case_id=test_case_id,
        is_selected=update_data.is_selected,
    )
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    return test_case

class BulkApprovalRequest(BaseModel):
    test_case_ids: list[uuid.UUID]

@router.post("/sessions/{session_id}/test-cases/approve", response_model=List[TestCaseResponse])
async def bulk_approve_test_cases(
    session_id: uuid.UUID,
    approval_data: BulkApprovalRequest,
    test_case_repo: TestCaseRepository = Depends(get_test_case_repo),
):
    """Approve selected test cases. Only approved cases can be selected for execution."""
    updated_cases = await test_case_repo.bulk_approve_test_cases(
        session_id=session_id,
        test_case_ids=approval_data.test_case_ids,
    )
    return updated_cases

@router.post("/sessions/{session_id}/generate-script", response_model=TestScriptResponse)
async def generate_script(
    session_id: uuid.UUID,
    generation_service: GenerationService = Depends(get_generation_service),
):
    try:
        script = await generation_service.generate_script_for_session(session_id)
        return script
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
