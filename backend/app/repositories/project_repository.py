import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.schemas.project import ProjectCreate


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_project(
        self,
        project_data: ProjectCreate,
    ) -> Project:
        project = Project(
            name=project_data.name,
            target_url=project_data.target_url,
            description=project_data.description,
        )

        self.session.add(project)

        await self.session.commit()
        await self.session.refresh(project)

        return project

    async def get_project_by_id(
        self,
        project_id: uuid.UUID,
    ) -> Project | None:
        statement = select(Project).where(
            Project.id == project_id,
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def list_projects(self) -> list[Project]:
        statement = (
            select(Project)
            .order_by(Project.created_at.desc())
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all())