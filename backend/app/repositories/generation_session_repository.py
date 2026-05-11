import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.generation_session import (
    GenerationSession,
    GenerationSessionStatus,
)
from app.models.test_case import TestCase


class GenerationSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_session(
        self,
        project_id: uuid.UUID,
        context_input: str,
    ) -> GenerationSession:
        generation_session = GenerationSession(
            project_id=project_id,
            context_input=context_input,
            status=GenerationSessionStatus.PENDING,
        )

        self.session.add(generation_session)

        await self.session.commit()
        await self.session.refresh(generation_session)

        return generation_session

    async def get_session_by_id(
        self,
        session_id: uuid.UUID,
    ) -> GenerationSession | None:
        statement = (
            select(GenerationSession)
            .options(
                selectinload(GenerationSession.test_cases),
                selectinload(GenerationSession.test_script),
            )
            .where(GenerationSession.id == session_id)
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def update_session_status(
        self,
        session_id: uuid.UUID,
        status: GenerationSessionStatus,
    ) -> GenerationSession | None:
        generation_session = await self.get_session_by_id(
            session_id,
        )

        if generation_session is None:
            return None

        generation_session.status = status

        await self.session.commit()
        await self.session.refresh(generation_session)

        return generation_session

    async def select_test_cases(
    self,
    session_id: uuid.UUID,
    selected_test_case_ids: list[uuid.UUID],
    ) -> GenerationSession | None:
        statement = select(TestCase).where(
            TestCase.session_id == session_id,
        )

        result = await self.session.execute(statement)

        test_cases = list(result.scalars().all())

        if not test_cases:
            return None

        for test_case in test_cases:
            test_case.is_selected = (
                test_case.id in selected_test_case_ids
            )

        await self.session.commit()

        return await self.get_session_by_id(session_id)