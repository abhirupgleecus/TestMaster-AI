import uuid
from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.test_case import TestCase
from app.schemas.test_case import TestCaseCreate


class TestCaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_test_cases(
        self,
        session_id: uuid.UUID,
        test_cases: list[TestCaseCreate],
    ) -> list[TestCase]:
        test_case_models = [
            TestCase(
                session_id=session_id,
                title=test_case.title,
                description=test_case.description,
                preconditions=test_case.preconditions,
                steps=[
                    step.model_dump()
                    for step in test_case.steps
                ],
                expected_output=test_case.expected_output,
                is_selected=test_case.is_selected,
                order_index=test_case.order_index,
            )
            for test_case in test_cases
        ]

        self.session.add_all(test_case_models)

        await self.session.commit()

        for test_case in test_case_models:
            await self.session.refresh(test_case)

        return test_case_models

    async def get_test_cases_by_session_id(
        self,
        session_id: uuid.UUID,
    ) -> list[TestCase]:
        statement = (
            select(TestCase)
            .where(TestCase.session_id == session_id)
            .order_by(TestCase.order_index.asc())
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all())

    async def get_selected_test_cases(
        self,
        session_id: uuid.UUID,
    ) -> list[TestCase]:
        statement = (
            select(TestCase)
            .where(
                TestCase.session_id == session_id,
                TestCase.is_selected.is_(True),
            )
            .order_by(TestCase.order_index.asc())
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all())
    
    async def update_test_case_selection(
        self,
        test_case_id: uuid.UUID,
        is_selected: bool,
    ) -> TestCase | None:
        statement = select(TestCase).where(
            TestCase.id == test_case_id,
        )

        result = await self.session.execute(
            statement,
        )

        test_case = result.scalar_one_or_none()

        if test_case is None:
            return None

        test_case.is_selected = is_selected

        await self.session.commit()
        await self.session.refresh(test_case)

        return test_case

    async def bulk_approve_test_cases(
        self,
        session_id: uuid.UUID,
        test_case_ids: list[uuid.UUID],
    ) -> list[TestCase]:
        """Approve specific test cases and reset any previously approved ones not in the list."""
        # First, unapprove all test cases for this session
        await self.session.execute(
            update(TestCase)
            .where(TestCase.session_id == session_id)
            .values(is_approved=False, is_selected=False)
        )

        # Then approve the selected ones
        if test_case_ids:
            await self.session.execute(
                update(TestCase)
                .where(
                    TestCase.session_id == session_id,
                    TestCase.id.in_(test_case_ids),
                )
                .values(is_approved=True)
            )

        await self.session.commit()

        # Return the refreshed full list
        return await self.get_test_cases_by_session_id(session_id)

    async def get_approved_and_selected_test_cases(
        self,
        session_id: uuid.UUID,
    ) -> list[TestCase]:
        """Only return test cases that are both approved AND selected for execution."""
        statement = (
            select(TestCase)
            .where(
                TestCase.session_id == session_id,
                TestCase.is_approved.is_(True),
                TestCase.is_selected.is_(True),
            )
            .order_by(TestCase.order_index.asc())
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all())