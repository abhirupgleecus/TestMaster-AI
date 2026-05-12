import json
import base64
import re
from pathlib import Path

from google import genai
from google.genai.types import GenerateContentConfig

from app.core.config import settings
from app.prompts.playwright_prompts import (
    build_playwright_generation_prompt,
)
from app.prompts.report_prompts import (
    build_test_report_prompt,
)
from app.prompts.test_case_prompts import (
    build_test_case_generation_prompt,
    validate_test_case_count,
)
from app.schemas.llm import (
    TestCaseGenerationResponse,
    TestReportGenerationResponse,
)
from app.models.test_execution import (
    TestExecution,
)
from app.models.test_case import TestCase
from app.models.project import Project


class LLMService:
    def __init__(self) -> None:
        self.client = genai.Client(
            api_key=settings.gemini_api_key,
        )

        self.model_name = (
            settings.gemini_model
        )

    def _harden_generated_playwright_script(
        self,
        script_content: str,
    ) -> str:
        unsafe_highlight_pattern = re.compile(
            r"async highlight\(locator: Locator\)\s*\{\s*await locator\.evaluate\(\(el: HTMLElement\) => \{\s*el\.style\.border = '2px solid red';\s*el\.style\.backgroundColor = 'yellow';\s*\}\);\s*\}",
            re.DOTALL,
        )

        safe_highlight_helper = """
  async highlight(locator: Locator) {
    const handle = await locator.first().elementHandle({ timeout: 1200 }).catch(() => null);
    if (!handle) return;
    await handle.evaluate((el: HTMLElement) => {
      el.style.border = '2px solid red';
      el.style.backgroundColor = 'yellow';
    }).catch(() => null);
  }""".strip("\n")

        hardened_script = unsafe_highlight_pattern.sub(
            safe_highlight_helper,
            script_content,
        )

        return hardened_script

    def _clean_json_response(
        self,
        response_text: str,
    ) -> str:
        cleaned = response_text.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned.removeprefix(
                "```json"
            )

        if cleaned.endswith("```"):
            cleaned = cleaned.removesuffix(
                "```"
            )

        return cleaned.strip()

    async def _generate_json_response(
        self,
        prompt: str,
        image_path: str | None = None,
    ) -> dict:
        contents = [prompt]
        
        if image_path:
            image_file = Path(image_path)
            if image_file.exists():
                with open(image_file, "rb") as f:
                    image_data = base64.b64encode(f.read()).decode("utf-8")
                
                contents.append({
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": image_data
                    }
                })

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=GenerateContentConfig(
                temperature=0.2,
                response_mime_type=(
                    "application/json"
                ),
            ),
        )

        if not response.text:
            raise ValueError(
                "Gemini returned empty response."
        )

        cleaned_response = (
            self._clean_json_response(
                response.text
            )
        )

        return json.loads(cleaned_response)

    async def _generate_text_response(
        self,
        prompt: str,
    ) -> str:
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=GenerateContentConfig(
                temperature=0.2,
                response_mime_type="text/plain",
            ),
        )

        if not response.text:
            raise ValueError(
                "Gemini returned empty response."
            )

        return response.text.strip()

    async def generate_test_cases(
        self,
        project: Project,
        context_input: str,
        screenshot_path: str | None = None,
    ) -> TestCaseGenerationResponse:
        prompt = (
            build_test_case_generation_prompt(
                project_name=project.name,
                target_url=project.target_url,
                context_input=context_input,
            )
        )

        response_json = (
            await self._generate_json_response(
                prompt,
                image_path=screenshot_path
            )
        )

        validated_response = (
            TestCaseGenerationResponse(
                **response_json
            )
        )

        if not validate_test_case_count(
            validated_response.test_cases
        ):
            raise ValueError(
                "Generated test case count "
                "is outside allowed range."
            )

        return validated_response

    async def generate_playwright_script(
        self,
        target_url: str,
        test_cases: list[TestCase],
    ) -> str:
        prompt = (
            build_playwright_generation_prompt(
                target_url=target_url,
                test_cases=test_cases,
            )
        )

        content = await self._generate_text_response(
            prompt
        )

        content = self._harden_generated_playwright_script(
            content
        )

        if "@playwright/test" not in content or "test(" not in content:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                "Generated Playwright script is missing '@playwright/test' "
                "or a 'test(' block. This will likely cause discovery failure. "
                f"First 500 chars: {content[:500]}"
            )

        return content

    async def generate_test_report(
        self,
        execution: TestExecution,
        structured_execution_context: dict,
    ) -> TestReportGenerationResponse:
        prompt = build_test_report_prompt(
            execution,
            structured_execution_context,
        )

        response_json = (
            await self._generate_json_response(
                prompt
            )
        )

        return TestReportGenerationResponse(
            **response_json
        )
