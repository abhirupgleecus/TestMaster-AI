from app.models.test_execution import (
    TestExecution,
)


def build_test_report_prompt(
    execution: TestExecution,
) -> str:
    return f"""
You are a senior QA automation analyst.

Your task is to analyze Playwright execution results
and generate a concise structured test report.

Execution Status:
{execution.status.value}

Execution Metrics:
- Total Tests: {execution.total_tests}
- Passed Tests: {execution.passed_tests}
- Failed Tests: {execution.failed_tests}
- Skipped Tests: {execution.skipped_tests}
- Duration (ms): {execution.duration_ms}

Error Log:
{execution.error_log}

Playwright Results:
{execution.playwright_json}

Requirements:
- Generate concise and accurate analysis
- Summarize overall execution quality
- Identify key failures if present
- Do NOT invent issues not present in the data
- Base analysis ONLY on provided execution results
- Keep the report operational and actionable
- Avoid unnecessary verbosity

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