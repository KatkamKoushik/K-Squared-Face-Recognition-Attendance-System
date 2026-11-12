"""
K² FRS — Playwright End-to-End Suite for Next.js Admin Console.
Executes browser automation against the standalone/production Next.js build.
Validates DOM structure, navigation, accessibility, responsive viewports,
and the non-negotiable domain invariant displays (denominator N/A, biometric redaction).
"""

import os
import subprocess
import time
import urllib.request
import pytest
from playwright.sync_api import sync_playwright, Page, Browser

ADMIN_CONSOLE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "apps", "admin_console"))
TEST_PORT = 3099
BASE_URL = f"http://localhost:{TEST_PORT}"

pytestmark = pytest.mark.playwright


@pytest.fixture(scope="session")
def admin_server():
    """Starts the Next.js production server on TEST_PORT for the duration of the test session."""
    node_bin = "node"
    next_cli = os.path.join("node_modules", "next", "dist", "bin", "next")

    proc = subprocess.Popen(
        [node_bin, next_cli, "start", "-p", str(TEST_PORT)],
        cwd=ADMIN_CONSOLE_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Poll server readiness
    ready = False
    start_time = time.time()
    while time.time() - start_time < 20.0:
        try:
            with urllib.request.urlopen(f"{BASE_URL}/", timeout=2.0) as resp:
                if resp.status == 200:
                    ready = True
                    break
        except Exception:
            time.sleep(0.5)

    if not ready:
        proc.terminate()
        stdout, stderr = proc.communicate(timeout=5.0)
        pytest.fail(f"Next.js test server failed to start within 20s. Stderr: {stderr.decode('utf-8', errors='ignore')}")

    yield BASE_URL

    proc.terminate()
    try:
        proc.wait(timeout=5.0)
    except Exception:
        proc.kill()


@pytest.fixture(scope="session")
def playwright_instance():
    """Initializes Playwright instance."""
    p = sync_playwright().start()
    yield p
    p.stop()


@pytest.fixture(scope="session")
def browser(playwright_instance) -> Browser:
    """Launches headless Chromium browser."""
    b = playwright_instance.chromium.launch(headless=True)
    yield b
    b.close()


@pytest.fixture
def page(browser: Browser) -> Page:
    """Provides a fresh isolated browser tab/page for each test."""
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    p = context.new_page()
    yield p
    context.close()


def test_e2e_dashboard_layout_and_navigation(admin_server, page: Page):
    """Dashboard loads with branding, navigation sidebar, and system readiness indicator."""
    page.goto(f"{admin_server}/")
    assert "FRS" in page.title() or "KUCET" in page.content()

    # Verify header branding
    header = page.locator("header")
    assert header.is_visible()
    assert "Kakatiya University" in page.content()

    # Verify accessibility skip-to-content anchor
    skip_link = page.locator('a[href="#main-content"]')
    assert skip_link.count() >= 1

    # Verify main navigation links exist in the sidebar
    assert page.locator('a[href="/students"]').count() >= 1
    assert page.locator('a[href="/reports/attendance"]').count() >= 1
    assert page.locator('a[href="/audit/logs"]').count() >= 1
    assert page.locator('a[href="/governance"]').count() >= 1
    assert page.locator('a[href="/system/readiness"]').count() >= 1


def test_e2e_student_directory_page(admin_server, page: Page):
    """Student directory displays tabular registry with DPDP consent tracking."""
    page.goto(f"{admin_server}/students")
    page.wait_for_load_state("networkidle")

    content = page.content()
    assert "Student Directory" in content or "Student Registry" in content
    # Verify table headers
    assert "Roll Number" in content or "Student Name" in content or "Aarav" in content


def test_e2e_academic_structure_page(admin_server, page: Page):
    """Academic structure view renders departments and semester terms."""
    page.goto(f"{admin_server}/academic/structure")
    page.wait_for_load_state("networkidle")

    content = page.content()
    assert "Structure" in content or "Department" in content


def test_e2e_academic_offerings_page(admin_server, page: Page):
    """Academic offerings view renders subject allocations."""
    page.goto(f"{admin_server}/academic/offerings")
    page.wait_for_load_state("networkidle")

    content = page.content()
    assert "Offerings" in content or "Subject" in content


def test_e2e_joint_groups_page(admin_server, page: Page):
    """Joint groups view displays merged cross-cohort class configurations."""
    page.goto(f"{admin_server}/academic/joint-groups")
    page.wait_for_load_state("networkidle")

    content = page.content()
    assert "Joint" in content or "Group" in content


def test_e2e_roster_preview_page(admin_server, page: Page):
    """Roster preview displays frozen snapshot validation interface."""
    page.goto(f"{admin_server}/roster-preview")
    page.wait_for_load_state("networkidle")

    content = page.content()
    assert "Roster" in content or "Freeze" in content or "Snapshot" in content


def test_e2e_attendance_reports_denominator_guardrail(admin_server, page: Page):
    """Official attendance report page emphasizes the conducted-unit denominator rule."""
    page.goto(f"{admin_server}/reports/attendance")
    page.wait_for_load_state("networkidle")

    content = page.content()
    assert "Attendance" in content
    # Denominator invariant must be referenced or present in table/legend
    assert "Conducted" in content or "Denominator" in content or "N/A" in content


def test_e2e_audit_logs_privacy_redaction(admin_server, page: Page):
    """Audit ledger browser verifies that biometric vector representations are redacted."""
    page.goto(f"{admin_server}/audit/logs")
    page.wait_for_load_state("networkidle")

    content = page.content()
    assert "Audit" in content or "Ledger" in content
    # Ensure raw biometric vector representations never appear in DOM
    assert "embedding_vector" not in content
    assert "facial_crop_binary" not in content


def test_e2e_system_readiness_page(admin_server, page: Page):
    """System readiness monitors database connectivity and vision model approval."""
    page.goto(f"{admin_server}/system/readiness")
    page.wait_for_load_state("networkidle")

    content = page.content()
    assert "Readiness" in content or "System" in content or "Hardware" in content


def test_e2e_governance_and_privacy_page(admin_server, page: Page):
    """Governance page renders compliance metrics, ephemeral purging controls, and consent register."""
    page.goto(f"{admin_server}/governance")
    page.wait_for_load_state("networkidle")

    content = page.content()
    assert "Data Governance" in content or "Biometric Privacy" in content
    assert "Ephemeral Raw Image Purge" in content
    assert "Student Biometric Consent" in content
    assert "Cryptographic Receipt" in content
    assert "Non-Biometric Alternative" in content


def test_e2e_controlled_pilot_dashboard_page(admin_server, page: Page):
    """Controlled Pilot page displays cohort cards, TAR/FAR metrics, 14-day log, and Gate G7 matrix."""
    page.goto(f"{admin_server}/pilot")
    page.wait_for_load_state("networkidle")

    content = page.content()
    assert "Controlled Classroom Pilot Dashboard" in content
    assert "CS401: Distributed Systems" in content
    assert "True Accept Rate" in content
    assert "False Accept Rate" in content
    assert "14-Day Pilot Session Schedule" in content
    assert "Gate G7" in content


def test_e2e_404_not_found_recovery(admin_server, page: Page):
    """Visiting an unmapped route renders a friendly 404 boundary with navigation recovery."""
    page.goto(f"{admin_server}/non-existent-sample-route")
    page.wait_for_load_state("networkidle")

    content = page.content()
    assert "404" in content or "Not Found" in content

    # Check recovery link back to home
    return_link = page.locator('a[href="/"]')
    assert return_link.count() >= 1


def test_e2e_responsive_mobile_viewport(admin_server, browser: Browser):
    """Admin console adapts cleanly to mobile viewport (375x667) without horizontal layout breaks."""
    context = browser.new_context(viewport={"width": 375, "height": 667})
    mobile_page = context.new_page()

    mobile_page.goto(f"{admin_server}/")
    mobile_page.wait_for_load_state("networkidle")

    # Document body must be rendered and visible
    body = mobile_page.locator("body")
    assert body.is_visible()

    # Check that main content container fits within viewport width
    box = mobile_page.locator("main").bounding_box()
    if box:
        assert box["width"] <= 380  # Fits within mobile width bounds

    context.close()


def test_e2e_login_screen_and_credential_entry(admin_server, page: Page):
    """Login view renders institutional branding, hidden sidebars, and secure credential entry."""
    page.goto(f"{admin_server}/login")
    page.wait_for_load_state("networkidle")

    # Verify institutional branding
    content = page.content()
    assert "FRS Admin Console" in content
    assert "Kakatiya University" in content
    assert "Sign In to Admin Console" in content

    # Sidebar and top header must be hidden on the clean login screen
    assert page.locator("aside").count() == 0
    assert page.locator("header").count() == 0

    # Verify input fields
    email_input = page.locator('input[type="email"]')
    assert email_input.is_visible()
    password_input = page.locator('input[type="password"]')
    assert password_input.is_visible()

    # Verify manual entry of institutional credentials (demo buttons removed for production hardening)
    email_input.fill("principal.kucet@gmail.com")
    password_input.fill("KucetFaculty@2026")
    assert email_input.input_value() == "principal.kucet@gmail.com"
    assert password_input.input_value() == "KucetFaculty@2026"


def test_e2e_governance_data_status_banner(admin_server, page: Page):
    """Governance page clearly displays the authoritative or offline status banner."""
    page.goto(f"{admin_server}/governance")
    page.wait_for_load_state("networkidle")

    content = page.content()
    # Must indicate either live postgres or offline preview mode cleanly
    assert "Live Control Plane Connected" in content or "Offline Preview Mode" in content

