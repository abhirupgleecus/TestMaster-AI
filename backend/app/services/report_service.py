import re
from pathlib import Path

from app.core.config import settings
from app.models.project import (
    Project,
)
from app.models.test_case import (
    TestCase,
)
from app.models.test_execution import (
    TestExecution,
)
from app.models.test_report import (
    TestReportStatus,
)
from app.services.llm_service import (
    LLMService,
)


ANSI_ESCAPE_PATTERN = re.compile(
    r"\x1B\[[0-?]*[ -/]*[@-~]"
)


class ReportService:
    def __init__(self) -> None:
        self.llm_service = LLMService()
        self.workspace_path = Path(
            settings.playwright_workspace_path
        ).resolve()
        self.reports_path = (
            self.workspace_path
            / "reports"
        ).resolve()
        self.test_results_path = (
            self.workspace_path
            / "test-results"
        ).resolve()

    def determine_report_status(
        self,
        execution: TestExecution,
    ) -> TestReportStatus:
        if execution.total_tests is None or execution.total_tests == 0:
            return TestReportStatus.FAILED

        if execution.failed_tests and execution.failed_tests > 0:
            return TestReportStatus.FAILED

        return TestReportStatus.PASSED

    def normalize_confidence_score(
        self,
        confidence_score: float | None,
    ) -> float:
        if confidence_score is None:
            return 0.5

        return max(
            0.0,
            min(confidence_score, 1.0),
        )

    def _strip_ansi(
        self,
        text: str | None,
    ) -> str:
        if not text:
            return ""

        return ANSI_ESCAPE_PATTERN.sub(
            "",
            text,
        )

    def _normalize_title(
        self,
        title: str | None,
    ) -> str:
        if not title:
            return ""

        normalized = re.sub(
            r"[^a-z0-9]+",
            " ",
            title.lower(),
        )

        return normalized.strip()

    def _artifact_url_from_path(
        self,
        artifact_path: str | None,
    ) -> str | None:
        if not artifact_path:
            return None

        path_obj = Path(artifact_path).resolve()

        if self.test_results_path in path_obj.parents:
            relative = path_obj.relative_to(
                self.test_results_path
            ).as_posix()
            return (
                f"/artifacts/test-results/{relative}"
            )

        if self.reports_path in path_obj.parents:
            relative = path_obj.relative_to(
                self.reports_path
            ).as_posix()
            return f"/artifacts/reports/{relative}"

        return None

    def _build_artifact_payload(
        self,
        attachments: list[dict] | None,
    ) -> tuple[list[dict], list[dict]]:
        artifacts: list[dict] = []
        screenshots: list[dict] = []

        for attachment in attachments or []:
            path = attachment.get("path")
            url = self._artifact_url_from_path(path)

            artifact = {
                "name": attachment.get("name"),
                "content_type": (
                    attachment.get("contentType")
                ),
                "path": path,
                "url": url,
            }

            artifacts.append(artifact)

            if (
                attachment.get("contentType", "")
                .startswith("image/")
            ):
                screenshots.append(artifact)

        return artifacts, screenshots

    def _summarize_error(
        self,
        result: dict,
    ) -> str | None:
        raw_message = (
            result.get("error", {}).get("message")
            or ""
        )

        if not raw_message:
            errors = result.get("errors") or []
            if errors:
                raw_message = (
                    errors[0].get("message") or ""
                )

        cleaned = self._strip_ansi(raw_message)
        cleaned = re.sub(
            r"\s+",
            " ",
            cleaned,
        ).strip()

        if not cleaned:
            return None

        if (
            "locator.evaluate:"
            in cleaned
            and "highlight"
            in cleaned.lower()
        ):
            return (
                "The generated highlight helper timed out while waiting "
                "for the target locator, so the functional interaction "
                "never completed."
            )

        if "Expected pattern: not /Login.aspx/" in cleaned:
            return (
                "The assertion expected navigation away from Login.aspx, "
                "but the page stayed on the login URL during the check."
            )

        if "Call log:" in cleaned:
            cleaned = cleaned.split(
                "Call log:",
                1,
            )[0].strip()

        return cleaned[:500]

    def _extract_playwright_specs(
        self,
        playwright_json: dict | None,
    ) -> list[dict]:
        if not playwright_json:
            return []

        collected_specs: list[dict] = []

        def visit_suite(suite: dict) -> None:
            for spec in suite.get("specs", []):
                collected_specs.append(spec)

            for child in suite.get("suites", []):
                visit_suite(child)

        for suite in playwright_json.get("suites", []):
            visit_suite(suite)

        executed_specs: list[dict] = []

        for index, spec in enumerate(collected_specs):
            tests = spec.get("tests") or []
            first_test = tests[0] if tests else {}
            results = first_test.get("results") or []
            latest_result = (
                results[-1] if results else {}
            )

            raw_status = (
                latest_result.get("status")
                or first_test.get("status")
                or "unknown"
            )

            normalized_status = raw_status
            if raw_status == "expected":
                normalized_status = "passed"
            elif raw_status in ("unexpected", "failed", "timedOut"):
                normalized_status = "failed"

            artifacts, screenshots = (
                self._build_artifact_payload(
                    latest_result.get("attachments")
                )
            )

            executed_specs.append(
                {
                    "spec_index": index,
                    "title": spec.get("title"),
                    "status": normalized_status,
                    "raw_status": raw_status,
                    "duration_ms": latest_result.get(
                        "duration"
                    ),
                    "error_summary": (
                        self._summarize_error(
                            latest_result
                        )
                    ),
                    "artifacts": artifacts,
                    "screenshots": screenshots,
                    "location": {
                        "file": (
                            latest_result.get(
                                "errorLocation",
                                {},
                            ).get("file")
                            or spec.get("file")
                        ),
                        "line": (
                            latest_result.get(
                                "errorLocation",
                                {},
                            ).get("line")
                            or spec.get("line")
                        ),
                    },
                }
            )

        return executed_specs

    def _build_test_case_result(
        self,
        test_case: TestCase | None,
        executed_spec: dict | None,
    ) -> dict:
        title = (
            test_case.title
            if test_case is not None
            else (
                executed_spec.get("title")
                if executed_spec is not None
                else "Unknown Test Case"
            )
        )

        if executed_spec is None:
            return {
                "planned_title": title,
                "executed_title": None,
                "status": "not_run",
                "raw_status": "not_run",
                "duration_ms": None,
                "description": (
                    test_case.description
                    if test_case is not None
                    else None
                ),
                "preconditions": (
                    test_case.preconditions
                    if test_case is not None
                    else None
                ),
                "expected_output": (
                    test_case.expected_output
                    if test_case is not None
                    else None
                ),
                "steps": (
                    test_case.steps
                    if test_case is not None
                    else []
                ),
                "observed_outcome": (
                    "No matching executed Playwright test result was found "
                    "for this selected test case."
                ),
                "failure_reason": (
                    "Selected test case did not map to an executed Playwright spec."
                ),
                "screenshots": [],
                "artifacts": [],
                "location": None,
            }

        status = executed_spec["status"]
        observed_outcome = (
            "Playwright completed this test without a reported error."
            if status == "passed"
            else (
                executed_spec["error_summary"]
                or "Playwright reported a failure without a detailed summary."
            )
        )

        return {
            "planned_title": title,
            "executed_title": executed_spec.get("title"),
            "status": status,
            "raw_status": executed_spec.get(
                "raw_status"
            ),
            "duration_ms": executed_spec.get(
                "duration_ms"
            ),
            "description": (
                test_case.description
                if test_case is not None
                else None
            ),
            "preconditions": (
                test_case.preconditions
                if test_case is not None
                else None
            ),
            "expected_output": (
                test_case.expected_output
                if test_case is not None
                else None
            ),
            "steps": (
                test_case.steps
                if test_case is not None
                else []
            ),
            "observed_outcome": observed_outcome,
            "failure_reason": (
                executed_spec.get("error_summary")
                if status != "passed"
                else None
            ),
            "screenshots": executed_spec.get(
                "screenshots",
                [],
            ),
            "artifacts": executed_spec.get(
                "artifacts",
                [],
            ),
            "location": executed_spec.get("location"),
        }

    def _build_structured_execution_context(
        self,
        execution: TestExecution,
        selected_test_cases: list[TestCase],
        project: Project | None,
    ) -> dict:
        executed_specs = self._extract_playwright_specs(
            execution.playwright_json
        )

        unmatched_specs = executed_specs.copy()
        title_buckets: dict[str, list[dict]] = {}

        for spec in executed_specs:
            title_buckets.setdefault(
                self._normalize_title(spec["title"]),
                [],
            ).append(spec)

        executed_test_cases: list[dict] = []
        used_spec_indexes: set[int] = set()

        for selected_case in selected_test_cases:
            normalized_title = self._normalize_title(
                selected_case.title
            )

            matched_spec = None

            if title_buckets.get(normalized_title):
                matched_spec = title_buckets[
                    normalized_title
                ].pop(0)
            else:
                for spec in unmatched_specs:
                    if (
                        spec["spec_index"]
                        not in used_spec_indexes
                    ):
                        matched_spec = spec
                        break

            if matched_spec is not None:
                used_spec_indexes.add(
                    matched_spec["spec_index"]
                )

            executed_test_cases.append(
                self._build_test_case_result(
                    selected_case,
                    matched_spec,
                )
            )

        for spec in executed_specs:
            if spec["spec_index"] in used_spec_indexes:
                continue

            executed_test_cases.append(
                self._build_test_case_result(
                    None,
                    spec,
                )
            )

        report_artifacts = {
            "html_report_url": (
                self._artifact_url_from_path(
                    (
                        Path(
                            execution.playwright_html_path
                        )
                        / "index.html"
                    ).as_posix()
                    if execution.playwright_html_path
                    else None
                )
            ),
            "json_report_url": (
                f"/artifacts/reports/{execution.id}/results.json"
                if execution.playwright_json is not None
                else None
            ),
        }

        return {
            "project": {
                "name": (
                    project.name
                    if project is not None
                    else None
                ),
                "target_url": (
                    project.target_url
                    if project is not None
                    else None
                ),
            },
            "summary": {
                "selected_test_case_count": len(
                    selected_test_cases
                ),
                "executed_test_case_count": len(
                    executed_test_cases
                ),
                "passed_test_count": (
                    execution.passed_tests or 0
                ),
                "failed_test_count": (
                    execution.failed_tests or 0
                ),
                "skipped_test_count": (
                    execution.skipped_tests or 0
                ),
                "duration_ms": execution.duration_ms,
            },
            "report_artifacts": report_artifacts,
            "executed_test_cases": executed_test_cases,
        }

    def _build_fallback_summary(
        self,
        execution: TestExecution,
        structured_context: dict,
    ) -> tuple[str, list[str], list[str], list[str]]:
        executed_cases = structured_context[
            "executed_test_cases"
        ]
        passed_cases = [
            case["planned_title"]
            for case in executed_cases
            if case["status"] == "passed"
        ]
        failed_cases = [
            case
            for case in executed_cases
            if case["status"] == "failed"
        ]

        executive_summary = (
            f"{len(executed_cases)} test cases ran. "
            f"{len(passed_cases)} passed and {len(failed_cases)} failed. "
            "The deterministic execution data has been used because the AI summary "
            "could not be generated for this run."
        )

        highlights = []
        if passed_cases:
            highlights.append(
                "Passed cases: "
                + ", ".join(passed_cases[:5])
            )

        highlights.append(
            "The report includes testcase-level status and artifact evidence extracted directly from Playwright."
        )

        failures = [
            (
                f"{case['planned_title']}: "
                f"{case['failure_reason']}"
            )
            for case in failed_cases[:5]
        ]

        recommendations = [
            "Review the failing test cases below and use the attached screenshots and Playwright artifacts to validate the observed behavior.",
        ]

        if any(
            "highlight helper" in (
                case.get("failure_reason") or ""
            ).lower()
            for case in failed_cases
        ):
            recommendations.append(
                "Make highlight logic best-effort and non-blocking so evidence capture never causes functional test failure."
            )

        if any(
            "login.aspx" in (
                case.get("failure_reason") or ""
            ).lower()
            for case in failed_cases
        ):
            recommendations.append(
                "Validate popup/new-tab or external-destination behavior explicitly instead of assuming the current page URL must change."
            )

        return (
            executive_summary,
            highlights,
            failures,
            recommendations,
        )

    async def generate_report(
        self,
        execution: TestExecution,
        selected_test_cases: list[TestCase],
        project: Project | None = None,
    ) -> dict:
        structured_context = (
            self._build_structured_execution_context(
                execution=execution,
                selected_test_cases=selected_test_cases,
                project=project,
            )
        )

        llm_response = None

        try:
            llm_response = (
                await self.llm_service
                .generate_test_report(
                    execution,
                    structured_context,
                )
            )
        except Exception:
            llm_response = None

        normalized_status = (
            self.determine_report_status(
                execution,
            )
        )

        if llm_response is not None:
            normalized_confidence = (
                self.normalize_confidence_score(
                    llm_response.confidence_score,
                )
            )
            executive_summary = (
                llm_response.executive_summary
            )
            detailed_analysis = (
                llm_response
                .detailed_analysis
                .model_dump()
            )
        else:
            (
                executive_summary,
                highlights,
                failures,
                recommendations,
            ) = self._build_fallback_summary(
                execution,
                structured_context,
            )
            normalized_confidence = 0.45
            detailed_analysis = {
                "highlights": highlights,
                "failures": failures,
                "recommendations": recommendations,
            }

        if execution.total_tests is None or execution.total_tests == 0:
            executive_summary = (
                "CRITICAL: No tests were discovered or executed. "
                "This indicates a failure in test discovery or script generation. "
                f"Full Output: {execution.stdout}"
            )

        detailed_analysis.update(
            {
                "summary": structured_context[
                    "summary"
                ],
                "executed_test_cases": (
                    structured_context[
                        "executed_test_cases"
                    ]
                ),
                "report_artifacts": (
                    structured_context[
                        "report_artifacts"
                    ]
                ),
            }
        )

        return {
            "execution_id": execution.id,
            "executive_summary": executive_summary,
            "detailed_analysis": detailed_analysis,
            "overall_status": normalized_status,
            "confidence_score": normalized_confidence,
        }
