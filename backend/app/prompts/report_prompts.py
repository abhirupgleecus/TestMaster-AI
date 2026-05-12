import json

from app.models.test_execution import (
    TestExecution,
)
from app.prompts.reference_context import (
    build_report_reference_context,
)


def build_test_report_prompt(
    execution: TestExecution,
    structured_execution_context: dict,
) -> str:
    reference_context = (
        build_report_reference_context()
    )

    return f"""
You are a senior QA automation analyst.

Your task is to analyze Playwright execution results
and generate a concise but accurate structured test report.

Execution Status:
{execution.status.value}

Execution Metrics:
- Total Tests: {execution.total_tests}
- Passed Tests: {execution.passed_tests}
- Failed Tests: {execution.failed_tests}
- Skipped Tests: {execution.skipped_tests}
- Duration (ms): {execution.duration_ms}

Reference Context:
{reference_context}

Structured Execution Context:
{json.dumps(structured_execution_context, indent=2)}

Raw Error Log:
{execution.error_log}

Raw Playwright Results:
{execution.playwright_json}

Requirements:
- Generate concise and accurate analysis.
- Summarize overall execution quality using the exact pass/fail counts.
- Reference the actual executed test case titles from the structured execution context.
- Identify the main failure patterns and root causes if present.
- Do NOT invent issues not present in the data.
- Base analysis ONLY on the provided execution results and structured execution context.
- Keep the report operational and actionable.
- Avoid vague statements like "the suite is unstable" unless the concrete evidence clearly supports that wording.
- Treat deterministic execution facts (test case status, failure reason, artifact presence) as authoritative.
- Recommendations must be specific to the observed failures, especially locator strategy, login-flow prerequisites, popup/new-tab handling, or brittle assertions where applicable.

### FEW-SHOT EXAMPLE OF A GOOD REPORT:
{{
  "executive_summary": "8 test cases ran. 4 passed and 4 failed. The passing coverage confirmed the login page shell, local-account transition, username entry, and password masking. The failing cases were concentrated in login submission and support-link navigation, with 3 failures caused by a blocking highlight helper on the login button locator and 1 failure caused by asserting same-tab URL change for a support action that should be validated as external navigation or popup behavior.",
  "detailed_analysis": {{
    "highlights": [
      "The executed test cases clearly covered UI visibility, local-account transition, credential entry, validation, and support-link behavior.",
      "The failure cluster points to generated automation logic rather than a broad outage of the target page."
    ],
    "failures": [
      "Verify Successful Login with Valid Credentials timed out inside the highlight helper while waiting for the login button locator.",
      "Verify Contact Support Link failed because the assertion expected the current page URL to leave Login.aspx instead of validating popup/new-tab behavior."
    ],
    "recommendations": [
      "Make highlight logic best-effort and non-blocking so visual traceability never becomes the reason a functional test fails.",
      "Use deterministic login-button locators from the target page and validate external links with popup/new-tab or href assertions instead of same-tab URL assumptions."
    ]
  }},
  "overall_status": "failed",
  "confidence_score": 0.94
}}

IMPORTANT:
- Return ONLY valid JSON
- Do NOT wrap the response in markdown
- Do NOT include explanations
- Do NOT include extra text

Return JSON in this exact structure:

{{
  "executive_summary": "Short summary",
  "detailed_analysis": {{
    "highlights": [
      "Key observation"
    ],
    "failures": [
      "Failure summary"
    ],
    "recommendations": [
      "Suggested improvement"
    ]
  }},
  "overall_status": "passed",
  "confidence_score": 0.95
}}
""".strip()
