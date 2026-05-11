import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectResponse

router = APIRouter()

def get_project_repo(db: AsyncSession = Depends(get_db)) -> ProjectRepository:
    return ProjectRepository(db)

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    repo: ProjectRepository = Depends(get_project_repo),
):
    return await repo.create_project(project_data)

@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    repo: ProjectRepository = Depends(get_project_repo),
):
    return await repo.list_projects()

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    repo: ProjectRepository = Depends(get_project_repo),
):
    project = await repo.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
