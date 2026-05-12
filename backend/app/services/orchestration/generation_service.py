import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import (
    GenerationSessionRepository,
    TestCaseRepository,
    TestScriptRepository,
)
from app.schemas.test_case import (
    TestCaseCreate,
)

from app.services.llm_service import (
    LLMService,
)
from app.services.playwright_service import (
    PlaywrightService,
)


class GenerationService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.llm_service = LLMService()
        self.playwright_service = PlaywrightService()

        self.generation_session_repository = (
            GenerationSessionRepository(
                session,
            )
        )

        self.test_case_repository = (
            TestCaseRepository(
                session,
            )
        )

        self.test_script_repository = (
            TestScriptRepository(
                session,
            )
        )

    async def generate_test_cases_for_session(
        self,
        session_id: uuid.UUID,
        context_input: str,
    ):
        generation_session = (
            await self
            .generation_session_repository
            .get_session_by_id(
                session_id,
            )
        )

        if generation_session is None:
            raise ValueError(
                "Generation session not found."
            )

        project = generation_session.project

        # Phase 1: Visual Discovery
        # Capture a screenshot of the landing page to provide visual context to the LLM
        screenshot_filename = f"discovery_{session_id}.png"
        screenshot_path = await self.playwright_service.capture_screenshot(
            url=project.target_url,
            filename=screenshot_filename
        )

        # Phase 2: Synthesis with Visual Context
        llm_response = (
            await self.llm_service
            .generate_test_cases(
                project=project,
                context_input=context_input,
                screenshot_path=screenshot_path
            )
        )

        test_case_creates = []

        for test_case in (
            llm_response.test_cases
        ):
            test_case_create = (
                TestCaseCreate(
                    generation_session_id=(
                        generation_session.id
                    ),

                    title=test_case.title,

                    description=(
                        test_case.description
                    ),

                    preconditions=(
                        test_case.preconditions
                    ),

                    steps=test_case.steps,

                    expected_output=(
                        test_case.expected_output
                    ),

                    is_selected=(
                        test_case.is_selected
                    ),

                    order_index=(
                        test_case.order_index
                    ),
                )
            )

            test_case_creates.append(
                test_case_create
            )

        created_test_cases = (
            await self
            .test_case_repository
            .create_test_cases(
                generation_session.id,
                test_case_creates,
            )
        )

        return created_test_cases

    async def generate_script_for_session(
        self,
        session_id: uuid.UUID,
    ):
        generation_session = (
            await self
            .generation_session_repository
            .get_session_by_id(
                session_id,
            )
        )

        if generation_session is None:
            raise ValueError(
                "Generation session not found."
            )

        selected_test_cases = (
            await self
            .test_case_repository
            .get_approved_and_selected_test_cases(
                generation_session.id,
            )
        )

        if not selected_test_cases:
            raise ValueError(
                "No approved and selected test cases found."
            )

        playwright_script = (
            await self.llm_service
            .generate_playwright_script(
                target_url=(
                    generation_session
                    .project
                    .target_url
                ),

                test_cases=(
                    selected_test_cases
                ),
            )
        )

        script_file_path = (
            f"generated_{generation_session.id}"
            ".spec.ts"
        )

        created_script = (
            await self
            .test_script_repository
            .create_or_update_script(
                session_id=(
                    generation_session.id
                ),

                script_content=(
                    playwright_script
                ),

                file_path=(
                    script_file_path
                ),
            )
        )

        return created_script