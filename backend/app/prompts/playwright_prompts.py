from app.models.test_case import TestCase


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

    return f"""
You are a senior Playwright automation engineer.

Your task is to generate a complete,
production-quality Playwright TypeScript test file.

Target URL:
{target_url}

Selected Test Cases:
{joined_test_cases}

Requirements:
- Use Playwright test syntax
- Use TypeScript
- Generate a complete executable .spec.ts file
- Include all required imports
- Use clear test descriptions
- Use robust Playwright locators
- Prefer getByRole and getByTestId selectors
- Avoid brittle selectors whenever possible
- Use proper Playwright assertions
- Avoid arbitrary waitForTimeout usage
- Use async/await correctly
- Keep code readable and maintainable
- Generate deterministic automation flows

IMPORTANT:
- Return ONLY raw TypeScript code
- Do NOT wrap the response in markdown
- Do NOT include explanations
- Do NOT include commentary
- Do NOT include triple backticks

The generated file must be immediately executable
inside a Playwright project.
""".strip()