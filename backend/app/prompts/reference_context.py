from functools import lru_cache
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_CONTEXT_ROOT = (
    BACKEND_ROOT / "reference_context"
)

REFERENCE_FILE_CANDIDATES = {
    "features": [
        REFERENCE_CONTEXT_ROOT
        / "Feature Login functionality.txt",
        REPO_ROOT
        / "Feature Login functionality.txt",
    ],
    "pom": [
        REFERENCE_CONTEXT_ROOT
        / "package login_page_object_model;.txt",
        REPO_ROOT
        / "package login_page_object_model;.txt",
    ],
    "steps": [
        REFERENCE_CONTEXT_ROOT
        / "package login_step_definition;.txt",
        REPO_ROOT
        / "package login_step_definition;.txt",
    ],
    "runner": [
        REFERENCE_CONTEXT_ROOT
        / "package login_test_run;.txt",
        REPO_ROOT
        / "package login_test_run;.txt",
    ],
}


@lru_cache
def _read_reference_file(name: str) -> str:
    for path in REFERENCE_FILE_CANDIDATES[name]:
        if path.exists():
            return path.read_text(
                encoding="utf-8",
                errors="ignore",
            )

    return ""


def _excerpt_from_anchor(text: str, anchor: str, max_lines: int = 14) -> str:
    if not text:
        return ""

    start = text.lower().find(anchor.lower())
    if start == -1:
        return ""

    snippet = text[start:].splitlines()[:max_lines]
    return "\n".join(line.rstrip() for line in snippet).strip()


def _join_snippets(snippets: list[str]) -> str:
    return "\n\n".join(snippet for snippet in snippets if snippet)


@lru_cache
def build_test_case_reference_context() -> str:
    features = _read_reference_file("features")
    pom = _read_reference_file("pom")
    steps = _read_reference_file("steps")
    runner = _read_reference_file("runner")

    feature_examples = _join_snippets(
        [
            _excerpt_from_anchor(
                features,
                "Scenario: Verify Login Page Loads Successfully",
            ),
            _excerpt_from_anchor(
                features,
                "Scenario: Verify navigation to local login form",
            ),
            _excerpt_from_anchor(
                features,
                "Scenario: Verify successful login using valid credentials",
            ),
            _excerpt_from_anchor(
                features,
                "Scenario: Verify login with invalid username or password",
            ),
            _excerpt_from_anchor(
                features,
                "Scenario: Verify login with empty username and password",
            ),
            _excerpt_from_anchor(
                features,
                "Scenario: Verify the functionality of Contact support button",
            ),
        ]
    )

    locator_examples = _join_snippets(
        [
            _excerpt_from_anchor(pom, "@FindBy (how=How.XPATH, using=\"//input[@id='cplMainContent_LoginUser_UserName']\")"),
            _excerpt_from_anchor(pom, "@FindBy (how=How.XPATH, using=\"//input[@id='btnLogin']\")"),
            _excerpt_from_anchor(pom, "@FindBy (how=How.XPATH, using=\"//*[contains(text(),'Contact support')]\")"),
        ]
    )

    behavior_examples = _join_snippets(
        [
            _excerpt_from_anchor(steps, "@When(\"Click on Contact support button\")"),
            _excerpt_from_anchor(steps, "@Then(\"It should open the Onshore Technology Group contact us page in the new tab\")"),
            _excerpt_from_anchor(runner, "plugin = {"),
        ]
    )

    return (
        "REFERENCE FEATURE EXAMPLES FROM THE REAL LEGACY LOGIN SUITE:\n"
        f"{feature_examples}\n\n"
        "REFERENCE LOCATOR EXAMPLES FROM THE REAL PAGE OBJECT MODEL:\n"
        f"{locator_examples}\n\n"
        "REFERENCE BEHAVIOR / REPORTING EXAMPLES FROM THE REAL STEP DEFINITIONS AND RUNNER:\n"
        f"{behavior_examples}"
    ).strip()


@lru_cache
def build_playwright_reference_context() -> str:
    features = _read_reference_file("features")
    pom = _read_reference_file("pom")
    steps = _read_reference_file("steps")
    runner = _read_reference_file("runner")

    feature_examples = _join_snippets(
        [
            _excerpt_from_anchor(
                features,
                "Scenario: Verify successful login using valid credentials",
            ),
            _excerpt_from_anchor(
                features,
                "Scenario: Verify login with invalid username or password",
            ),
            _excerpt_from_anchor(
                features,
                "Scenario: Verify login with empty username and password",
            ),
            _excerpt_from_anchor(
                features,
                "Scenario: Verify the functionality of Contact support button",
            ),
            _excerpt_from_anchor(
                features,
                "Scenario: Verify Login with SSO button functionality",
            ),
        ]
    )

    implementation_examples = _join_snippets(
        [
            _excerpt_from_anchor(
                pom,
                "public void click_on_login_button() throws Exception",
                max_lines=28,
            ),
            _excerpt_from_anchor(
                pom,
                "public void click_on_contact_support_button() throws Exception",
                max_lines=18,
            ),
            _excerpt_from_anchor(
                pom,
                "public void login_should_successful_and_navigate_to_the_landing_page()",
                max_lines=12,
            ),
        ]
    )

    locator_examples = _join_snippets(
        [
            _excerpt_from_anchor(pom, "@FindBy (how=How.XPATH, using=\"//input[@id='cplMainContent_LoginUser_UserName']\")"),
            _excerpt_from_anchor(pom, "@FindBy (how=How.XPATH, using=\"//input[@id='cplMainContent_LoginUser_Password']\")"),
            _excerpt_from_anchor(pom, "@FindBy (how=How.XPATH, using=\"//input[@id='btnLogin']\")"),
            _excerpt_from_anchor(pom, "@FindBy (how=How.XPATH, using=\"//span[contains(text(),'You need to enter a username')]\")"),
            _excerpt_from_anchor(pom, "@FindBy (how=How.XPATH, using=\"//*[contains(text(),'Contact support')]\")"),
        ]
    )

    reporting_examples = _join_snippets(
        [
            _excerpt_from_anchor(steps, "@Then(\"Login should fail and display an error message as You need to enter a user name and you need to enter a password\")"),
            _excerpt_from_anchor(steps, "@Then(\"It should open the Onshore Technology Group contact us page in the new tab\")"),
            _excerpt_from_anchor(runner, "plugin = {"),
        ]
    )

    return (
        "REFERENCE FEATURE / BEHAVIOR EXAMPLES:\n"
        f"{feature_examples}\n\n"
        "REFERENCE LOCATORS / PAGE OBJECT EXAMPLES:\n"
        f"{locator_examples}\n\n"
        "REFERENCE IMPLEMENTATION EXAMPLES:\n"
        f"{implementation_examples}\n\n"
        "REFERENCE REPORTING EXAMPLES:\n"
        f"{reporting_examples}"
    ).strip()


@lru_cache
def build_report_reference_context() -> str:
    features = _read_reference_file("features")
    pom = _read_reference_file("pom")
    steps = _read_reference_file("steps")
    runner = _read_reference_file("runner")

    report_expectation_examples = _join_snippets(
        [
            _excerpt_from_anchor(
                features,
                "Scenario: Verify successful login using valid credentials",
            ),
            _excerpt_from_anchor(
                features,
                "Scenario: Verify login with invalid username or password",
            ),
            _excerpt_from_anchor(
                features,
                "Scenario: Verify login with empty username and password",
            ),
            _excerpt_from_anchor(
                features,
                "Scenario: Verify the functionality of Contact support button",
            ),
            _excerpt_from_anchor(
                pom,
                "public void it_should_open_the_onshore_technology_group_contact_us_page_in_the_new_tab()",
                max_lines=8,
            ),
            _excerpt_from_anchor(
                steps,
                "@Then(\"It should open the Onshore Technology Group contact us page in the new tab\")",
                max_lines=8,
            ),
            _excerpt_from_anchor(runner, "plugin = {"),
        ]
    )

    return (
        "REFERENCE BEHAVIOR AND REPORTING CONTEXT FROM THE REAL LOGIN ASSETS:\n"
        f"{report_expectation_examples}"
    ).strip()
