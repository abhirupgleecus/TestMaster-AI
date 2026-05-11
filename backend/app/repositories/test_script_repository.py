import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.test_script import (
    TestScript,
    TestScriptStatus,
)


class TestScriptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_or_update_script(
        self,
        session_id: uuid.UUID,
        script_content: str,
        file_path: str,
    ) -> TestScript:
        existing_script = await self.get_script_by_session_id(
            session_id,
        )

        if existing_script is not None:
            existing_script.script_content = script_content
            existing_script.file_path = file_path
            existing_script.status = (
                TestScriptStatus.GENERATED
            )

            await self.session.commit()
            await self.session.refresh(existing_script)

            return existing_script

        test_script = TestScript(
            session_id=session_id,
            script_content=script_content,
            file_path=file_path,
            status=TestScriptStatus.GENERATED,
        )

        self.session.add(test_script)

        await self.session.commit()
        await self.session.refresh(test_script)

        return test_script

    async def get_script_by_id(
        self,
        script_id: uuid.UUID,
    ) -> TestScript | None:
        statement = select(TestScript).where(
            TestScript.id == script_id,
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_script_by_session_id(
        self,
        session_id: uuid.UUID,
    ) -> TestScript | None:
        statement = select(TestScript).where(
            TestScript.session_id == session_id,
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def update_script_status(
        self,
        script_id: uuid.UUID,
        status: TestScriptStatus,
    ) -> TestScript | None:
        test_script = await self.get_script_by_id(
            script_id,
        )

        if test_script is None:
            return None

        test_script.status = status

        await self.session.commit()
        await self.session.refresh(test_script)

        return test_script