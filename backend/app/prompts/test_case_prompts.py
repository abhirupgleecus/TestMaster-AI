from app.prompts.reference_context import (
    build_test_case_reference_context,
)
from app.schemas.test_case import TestCaseCreate


def build_test_case_generation_prompt(
    project_name: str,
    target_url: str,
    context_input: str,
) -> str:
    reference_context = build_test_case_reference_context()

    return f"""
You are a senior QA automation engineer specializing in high-precision UI testing.

Your task is to generate structured UI test cases for a web application.

Project Name:
{project_name}

Target URL:
{target_url}

User Context:
{context_input}

Reference Context:
{reference_context}

### STYLE GUIDELINES (Based on Enterprise Standards):
1. **Atomic Scenarios**: Generate granular test cases for every small interaction. This includes:
   - Verifying field data entry AND field clearing when those controls are visible.
   - Verifying field attribute states (e.g. masked password, validation text, toggle behavior).
   - Positive and negative credential variations when the user context provides credentials or the page clearly supports login.
2. **Comprehensive UI Audit**: Include a specific test case to verify the presence and visibility of all key UI components that are actually visible on the current landing state.
3. **SSO & Auth Variations**: If SSO buttons or identity-provider actions are present, include only realistic navigation scenarios for them.
4. **Visual Flow**: Ensure steps describe both the action and the expected visual state change.
5. **Reuse Real Business Language**: When the reference feature examples clearly match the current page, reuse their scenario intent, naming style, and expected outcomes instead of inventing generic phrasing.
6. **Respect Navigation Behavior**:
   - For support, copyright, forgot-password, or SSO actions, describe the real expected destination carefully.
   - Prefer "opens in a new tab/window" or "redirects to provider/support page" when appropriate.
   - Do NOT assume the current page URL must always change in the same tab.
7. **Honor Prerequisites**: If the current page starts with an SSO-first view and requires a "Login with Local Account" transition, include that step before any username/password interactions.
8. **Use the User Context**: If credentials are supplied, include a valid-login scenario plus realistic invalid and empty-field scenarios anchored to those credentials.

### REFERENCE EXAMPLE (Match this granularity):
Scenario: Verify the functionality of username field by entering the data
Given User should launch the browser
When Enter the login URL and click on enter
Then Navigate to the login page
When Enter the data inside the username field
Then Username field should accept the data and it should be visible

Scenario: Verify the UI of login page
Given User should launch the browser
When Enter the login URL and click on enter
Then It should display the ValidationMaster title with logo
And It should display username field
And It should display password field
And It should display login button

### FEW-SHOT EXAMPLES (Follow this structure and specificity):
Example A:
- title: Verify successful login using valid credentials
- description: Ensure the user can switch to the local account form, enter valid credentials, and reach the landing page.
- preconditions: Login page is reachable and valid credentials are available.
- steps:
  - Click "Login with Local Account"
  - Enter valid Username
  - Enter valid Password
  - Click Login button
  - Handle any post-login continuation prompt only if it actually appears
- expected_output: Login should be successful and the user should navigate to the Landing page.

Example B:
- title: Verify login with empty username and password
- description: Ensure empty field validation appears when the local login form is submitted without credentials.
- preconditions: Login page is reachable and local account form is visible.
- steps:
  - Click "Login with Local Account"
  - Click Login button without entering credentials
  - Observe validation feedback for both fields
- expected_output: Validation message should be displayed for Username and Password.

Example C:
- title: Verify the functionality of Contact support button
- description: Ensure the Contact support action opens the expected support destination.
- preconditions: Login page is reachable and the Contact support control is visible.
- steps:
  - Click Contact support button/link
  - Observe whether a new tab/window opens or an external support page loads
  - Validate the support destination rather than assuming same-tab URL change
- expected_output: It should open the Onshore Technology Group contact us page in the new tab.

Requirements:
- Focus on realistic UI workflows.
- ANALYZE THE PROVIDED SCREENSHOT: Identify required prerequisite steps, such as clicking "Login with SSO", switching to local account, handling banners, or dismissing splash screens.
- Avoid redundant test cases.
- Generate between 5 and 12 test cases to ensure deep coverage of the landing/login state.
- Use clear automation-friendly language.
- Keep the plan tightly aligned to the page state that is visibly present right now. Do not invent hidden forms, pages, or flows.
- Prefer scenario titles that can be reused directly as executable Playwright test names later.

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
    return 5 <= len(test_cases) <= 12
