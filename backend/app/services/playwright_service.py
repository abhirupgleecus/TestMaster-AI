import asyncio
import json
import platform
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from app.core.config import settings


@dataclass
class PlaywrightExecutionResult:
    success: bool

    return_code: int

    stdout: str
    stderr: str

    playwright_json: dict | None

    total_tests: int | None
    passed_tests: int | None
    failed_tests: int | None
    skipped_tests: int | None

    duration_ms: int | None 

    json_report_path: str
    html_report_path: str


class PlaywrightService:
    def __init__(self) -> None:
        self.workspace_path = Path(
            settings.playwright_workspace_path
        )

        self.npx_command = (
            "npx.cmd"
            if platform.system() == "Windows"
            else "npx"
        )

        self.tests_root_path = (
            self.workspace_path
            / "tests"
        )

        self.generated_tests_path = (
            self.tests_root_path
            / "generated"
        )

        self.reports_path = (
            self.workspace_path
            / "reports"
        )

        self.discovery_path = (
            self.workspace_path
            / "discovery"
        )

        self.generated_tests_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.reports_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.discovery_path.mkdir(
            parents=True,
            exist_ok=True,
        )

    def get_script_path(
        self,
        session_id: UUID,
    ) -> Path:
        return (
            self.generated_tests_path
            / f"generated_{session_id}.spec.ts"
        )

    def get_relative_script_path(
        self,
        session_id: UUID,
    ) -> str:
        script_path = self.get_script_path(
            session_id,
        )

        relative_path = script_path.relative_to(
            self.tests_root_path
        )

        return relative_path.as_posix()

    def get_execution_report_paths(
        self,
        execution_id: UUID,
    ) -> tuple[Path, Path]:
        execution_report_dir = (
            self.reports_path
            / str(execution_id)
        )

        execution_report_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        json_report_path = (
            execution_report_dir
            / "results.json"
        )

        html_report_path = (
            execution_report_dir
            / "html"
        )

        return (
            json_report_path,
            html_report_path,
        )

    def write_script_file(
        self,
        session_id: UUID,
        script_content: str,
    ) -> str:
        script_path = self.get_script_path(
            session_id,
        )

        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Writing Playwright script to: {script_path}")

        script_path.write_text(
            script_content,
            encoding="utf-8",
        )

        return str(script_path)

    def load_json_report(
        self,
        json_report_path: Path,
    ) -> dict | None:
        if not json_report_path.exists():
            return None

        with open(
            json_report_path,
            "r",
            encoding="utf-8",
        ) as report_file:
            return json.load(report_file)

    def extract_execution_metrics(
        self,
        playwright_json: dict | None,
    ) -> tuple[
        int | None,
        int | None,
        int | None,
        int | None,
        int | None,
    ]:
        if playwright_json is None:
            return (
                None,
                None,
                None,
                None,
                None,
            )

        stats = playwright_json.get("stats")

        if not stats:
            return (
                None,
                None,
                None,
                None,
                None,
            )

        total_tests = (
            stats.get("expected", 0)
            + stats.get("unexpected", 0)
            + stats.get("skipped", 0)
            + stats.get("flaky", 0)
        )

        passed_tests = stats.get(
            "expected",
            0,
        )

        failed_tests = stats.get(
            "unexpected",
            0,
        )

        skipped_tests = stats.get(
            "skipped",
            0,
        )

        duration_ms = int(
            stats.get("duration", 0)
        )

        return (
            total_tests,
            passed_tests,
            failed_tests,
            skipped_tests,
            duration_ms,
        )

    async def execute_script(
        self,
        session_id: UUID,
        execution_id: UUID,
    ) -> PlaywrightExecutionResult:
        import subprocess
        import os

        script_path = self.get_relative_script_path(
            session_id,
        )

        (
            json_report_path,
            html_report_path,
        ) = self.get_execution_report_paths(
            execution_id,
        )

        env = {
            **dict(os.environ),
            "PLAYWRIGHT_JSON_REPORT_PATH": str(json_report_path),
            "PLAYWRIGHT_HTML_REPORT_PATH": str(html_report_path),
            # Also keep these for compatibility with default behaviors
            "PLAYWRIGHT_JSON_OUTPUT_NAME": str(json_report_path),
            "PLAYWRIGHT_HTML_REPORT": str(html_report_path),
            "PLAYWRIGHT_HTML_OPEN": "never",
        }

        def run_subprocess():
            cmd = [self.npx_command, "playwright", "test", script_path]
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Running Playwright command: {' '.join(cmd)} in {self.workspace_path}")
            
            return subprocess.run(
                cmd,
                cwd=str(self.workspace_path),
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=180,
            )

        try:
            result = await asyncio.to_thread(run_subprocess)
            stdout_text = result.stdout
            stderr_text = result.stderr
            return_code = result.returncode
        except subprocess.TimeoutExpired as e:
            return PlaywrightExecutionResult(
                success=False,
                return_code=-1,
                stdout=e.stdout if e.stdout else "",
                stderr="Playwright execution timed out.",
                playwright_json=None,
                total_tests=None,
                passed_tests=None,
                failed_tests=None,
                skipped_tests=None,
                duration_ms=None,
                json_report_path=str(json_report_path),
                html_report_path=str(html_report_path),
            )
        except Exception as e:
            return PlaywrightExecutionResult(
                success=False,
                return_code=-1,
                stdout="",
                stderr=f"Subprocess error: {str(e)}",
                playwright_json=None,
                total_tests=None,
                passed_tests=None,
                failed_tests=None,
                skipped_tests=None,
                duration_ms=None,
                json_report_path=str(json_report_path),
                html_report_path=str(html_report_path),
            )

        playwright_json = self.load_json_report(
            json_report_path,
        )

        (
            total_tests,
            passed_tests,
            failed_tests,
            skipped_tests,
            duration_ms,
        ) = self.extract_execution_metrics(
            playwright_json,
        )

        success = return_code == 0

        return PlaywrightExecutionResult(
            success=success,
            return_code=return_code,
            stdout=stdout_text,
            stderr=stderr_text,
            playwright_json=playwright_json,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
            duration_ms=duration_ms,
            json_report_path=str(json_report_path),
            html_report_path=str(html_report_path),
        )

    async def capture_screenshot(
        self,
        url: str,
        filename: str,
    ) -> str | None:
        import subprocess
        
        output_path = self.discovery_path / filename
        
        # We use playwright CLI to take a screenshot
        # --wait-for-timeout 3000 to allow for initial animations/SSO redirects
        cmd = [
            self.npx_command, 
            "playwright", 
            "screenshot", 
            "--viewport-size=1280,720",
            "--timeout=30000",
            url, 
            str(output_path)
        ]
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Capturing discovery screenshot for {url} to {output_path}")
        
        def run_cmd():
            return subprocess.run(
                cmd,
                cwd=str(self.workspace_path),
                capture_output=True,
                text=True,
                encoding="utf-8"
            )
            
        try:
            # Run discovery in a thread to avoid blocking the event loop
            result = await asyncio.to_thread(run_cmd)
            
            if result.returncode == 0 and output_path.exists():
                logger.info(f"Successfully captured screenshot: {output_path}")
                return str(output_path)
            else:
                logger.error(f"Failed to capture screenshot. Return code: {result.returncode}. Stderr: {result.stderr}")
                return None
        except Exception as e:
            logger.error(f"Error during screenshot capture: {str(e)}")
            return None