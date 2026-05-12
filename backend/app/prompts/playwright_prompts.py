from app.models.test_case import TestCase
from app.prompts.reference_context import (
    build_playwright_reference_context,
)


def build_playwright_generation_prompt(
    target_url: str,
    test_cases: list[TestCase],
) -> str:
    formatted_test_cases = []

    for test_case in test_cases:
        formatted_test_cases.append(
            f"""
Test Case:
Title: {test_case.title}

Description:
{test_case.description}

Preconditions:
{test_case.preconditions}

Steps:
{test_case.steps}

Expected Output:
{test_case.expected_output}
""".strip()
        )

    joined_test_cases = "\n\n".join(
        formatted_test_cases
    )

    reference_context = (
        build_playwright_reference_context()
    )

    return f"""
You are a senior Playwright automation engineer.

Your task is to generate a complete, production-quality Playwright TypeScript test file.

Target URL:
{target_url}

Selected Test Cases:
{joined_test_cases}

Reference Context:
{reference_context}

### CODING STANDARDS (Based on Enterprise Legacy Requirements):
1. **Page Object Model (POM)**: Organize the test logic using a `Page` class. Define locators in the constructor and actions as methods.
2. **Preserve Planned Titles**: Use the selected test case titles exactly as the final Playwright `test('...')` names unless a tiny formatting cleanup is absolutely necessary.
3. **Locator Accuracy First**:
   - Prefer stable ids, names, labels, or exact text that align with the real page.
   - Reuse locator intent from the reference page object model when it clearly matches the current page.
   - Avoid broad selectors like `img[src*="logo"]` or generic `button[id*="Login"]` when a more precise locator is available.
4. **Best-Effort Highlight Only**:
   - You MAY include a `highlight` helper for visual traceability.
   - The helper must NEVER fail the test and must NEVER block the test waiting on a missing/ambiguous locator.
   - Do NOT use a raw `await locator.evaluate(...)` pattern that can stall execution.
   - Wrap highlight behavior in `try/catch` and use a short timeout with `elementHandle()` or an equivalent non-blocking approach.
5. **Interaction Realism**:
   - If a page starts with an SSO-first state, switch to "Login with Local Account" before interacting with username/password fields.
   - For login flows, model the sequence shown in the selected test case steps rather than inventing shortcuts.
6. **Assertion Quality**:
   - Do not assert external link behavior with `expect(page).not.toHaveURL(/Login.aspx/)` alone.
   - For Contact Support, Copyright, Forgot Password, or SSO flows, validate the correct outcome: popup/new tab, external provider page, href, or real destination URL/content.
   - For empty-field validation, assert the actual validation messages or dedicated validation elements when available.
   - For successful login, assert a real post-login indicator or expected URL only when justified by the reference context or page behavior.
7. **Resilience**:
   - Handle optional intermediate post-login screens only if they appear, such as conflict/continuation dialogs noted in the reference context.
   - If an assertion depends on navigation in a new tab or popup, explicitly wait for that popup/page.
8. **Evidence-Friendly Output**:
   - Use clear test descriptions and deterministic steps so the generated Playwright artifacts are easy to interpret in reports.

### FEW-SHOT IMPLEMENTATION EXAMPLES (Adapt, do not copy blindly):
```typescript
import {{ test, expect, Page, Locator }} from '@playwright/test';

class LoginPage {{
  readonly page: Page;
  readonly usernameField: Locator;
  readonly passwordField: Locator;
  readonly loginButton: Locator;
  readonly contactSupportLink: Locator;

  constructor(page: Page) {{
    this.page = page;
    this.usernameField = page.locator('#cplMainContent_LoginUser_UserName');
    this.passwordField = page.locator('#cplMainContent_LoginUser_Password');
    this.loginButton = page.locator('#btnLogin');
    this.contactSupportLink = page.getByText(/Contact support/i);
  }}

  async highlight(locator: Locator) {{
    const handle = await locator.first().elementHandle({{ timeout: 1200 }}).catch(() => null);
    if (!handle) return;
    await handle.evaluate((el: HTMLElement) => {{
      el.style.border = '2px solid red';
      el.style.backgroundColor = 'yellow';
    }}).catch(() => null);
  }}

  async openContactSupport() {{
    const popupPromise = this.page.waitForEvent('popup').catch(() => null);
    await this.highlight(this.contactSupportLink);
    await this.contactSupportLink.click();
    const popup = await popupPromise;
    if (popup) {{
      await popup.waitForLoadState('domcontentloaded');
      await expect(popup).toHaveURL(/contact|onshore/i);
      return;
    }}
    await expect(this.contactSupportLink).toHaveAttribute('href', /contact|onshore/i);
  }}
}}
```

```typescript
test('Verify successful login using valid credentials', async ({{ page }}) => {{
  const loginPage = new LoginPage(page);
  await loginPage.page.goto('...');
  await loginPage.openLocalAccount();
  await loginPage.login('qatestuser1', 'admin123');
  await expect(page).toHaveURL(/Landing|MyPage|Home/i);
}});
```

Requirements:
- Use Playwright test syntax.
- Use TypeScript.
- Generate a complete executable `.spec.ts` file.
- Include all required imports.
- Use a single POM-oriented file.
- Keep selectors and assertions grounded in the selected test cases and reference context.

IMPORTANT:
- Return ONLY raw TypeScript code.
- Do NOT wrap the response in markdown.
- Do NOT include explanations.
- Do NOT include commentary.
- Do NOT include triple backticks.

The generated file must be immediately executable inside a Playwright project.
""".strip()
