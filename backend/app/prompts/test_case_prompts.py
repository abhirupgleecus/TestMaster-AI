from app.schemas.test_case import TestCaseCreate


def build_test_case_generation_prompt(
    project_name: str,
    target_url: str,
    context_input: str,
) -> str:
    return f"""
You are a senior QA automation engineer.

Your task is to generate structured UI test cases
for a web application.

Project Name:
{project_name}

Target URL:
{target_url}

User Context:
{context_input}

Generate concise, execution-oriented test cases
suitable for Playwright automation.

Requirements:
- Focus on realistic UI workflows
- ANALYZE THE PROVIDED SCREENSHOT: Identify any required prerequisite steps, such as clicking 'Login with SSO', handling cookie banners, or dismissing splash screens that are visible in the image.
- If the screenshot shows a login gateway (like an SSO button) that must be clicked to reach the main application, include that click as the first step in your test cases.
- Avoid redundant test cases
- Keep descriptions concise
- Include meaningful expected outcomes
- Generate between 5 and 10 test cases
- Ensure steps are logically ordered
- Use clear automation-friendly language

Each test case must contain:
- title
- description
- preconditions
- steps
- expected_output
- is_selected
- order_index

Each step must contain:
- step_number
- action
- expected_result

Set:
- is_selected = false

IMPORTANT:
- Return ONLY valid JSON
- Do NOT wrap the response in markdown
- Do NOT include explanations
- Do NOT include extra text

Return JSON in this exact structure:

{{
  "test_cases": [
    {{
      "title": "Example Test",
      "description": "Short description",
      "preconditions": "Required setup",
      "steps": [
        {{
          "step_number": 1,
          "action": "Open login page",
          "expected_result": "Login page is visible"
        }}
      ],
      "expected_output": "User logs in successfully",
      "is_selected": false,
      "order_index": 0
    }}
  ]
}}
""".strip()


def validate_test_case_count(
    test_cases: list[TestCaseCreate],
) -> bool:
    return 5 <= len(test_cases) <= 10