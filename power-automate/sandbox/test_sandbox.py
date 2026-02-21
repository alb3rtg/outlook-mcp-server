#!/usr/bin/env python3
"""
Sandbox Test Environment for Power Automate Email Manager

This simulates the Power Automate flow logic locally to validate
all components before deployment.
"""

import json
import re
import unittest
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum
import html


class FlowAction(Enum):
    KEEP = "keep"
    MOVE_ONLY = "move_to_promotional"
    UNSUBSCRIBE_AND_MOVE = "unsubscribe_and_move"
    DELETE = "delete"


@dataclass
class Email:
    id: str
    from_address: str
    subject: str
    body: str
    received_datetime: datetime
    is_read: bool = False
    folder: str = "Inbox"


@dataclass
class FlowResult:
    email_id: str
    action: FlowAction
    is_promotional: bool
    unsubscribe_link: Optional[str] = None
    is_safe_to_unsubscribe: bool = False
    safety_reason: Optional[str] = None
    moved_to_folder: Optional[str] = None
    http_request_made: bool = False
    http_request_url: Optional[str] = None


@dataclass
class PurgeResult:
    deleted_emails: list = field(default_factory=list)
    kept_emails: list = field(default_factory=list)
    report_generated: bool = False
    report_content: Optional[str] = None


# =============================================================================
# COMPONENT 1: Promotional Detection
# =============================================================================

PROMOTIONAL_KEYWORDS_SUBJECT = [
    'offer', 'discount', 'sale', 'deal', 'limited time',
    'act now', 'exclusive', 'free', 'promotion'
]

PROMOTIONAL_KEYWORDS_BODY = [
    'unsubscribe', 'promotional', 'marketing email', 'email preferences'
]


def detect_promotional(subject: str, body: str) -> bool:
    """
    Simulates Power Automate's Check_If_Promotional compose action.
    """
    subject_lower = subject.lower()
    body_lower = body.lower()

    for keyword in PROMOTIONAL_KEYWORDS_SUBJECT:
        if keyword in subject_lower:
            return True

    for keyword in PROMOTIONAL_KEYWORDS_BODY:
        if keyword in body_lower:
            return True

    return False


# =============================================================================
# COMPONENT 2: Sender Domain Extraction
# =============================================================================

def extract_sender_domain(from_address: str) -> str:
    """
    Simulates Power Automate's Extract_Sender_Domain compose action.
    Expression: if(contains(triggerBody()?['from'], '@'),
                   last(split(triggerBody()?['from'], '@')), '')
    """
    if '@' not in from_address:
        return ""

    # Handle formats like "Name <email@domain.com>" or just "email@domain.com"
    domain = from_address.split('@')[-1]
    # Clean up trailing > and spaces
    domain = domain.replace('>', '').replace(' ', '').strip().lower()
    return domain


# =============================================================================
# COMPONENT 3: Unsubscribe Link Extraction
# =============================================================================

def extract_unsubscribe_link(body: str) -> str:
    """
    Simulates Power Automate's Extract_Unsubscribe_Link compose action.
    Looks for href attributes containing "unsubscribe".
    """
    # Primary: Look for href containing "unsubscribe"
    pattern = r'href=["\']([^"\']*unsubscribe[^"\']*)["\']'
    matches = re.findall(pattern, body, re.IGNORECASE)

    if matches:
        # Return the first match that looks like a URL
        for match in matches:
            if match.startswith('http'):
                return match
        return matches[0] if matches else ""

    # Fallback: Look for any URL near "unsubscribe" text
    if 'unsubscribe' in body.lower():
        url_pattern = r'(https?://[^\s<>"\']+)'
        url_matches = re.findall(url_pattern, body, re.IGNORECASE)
        for url in url_matches:
            if 'unsubscribe' in url.lower():
                return url

    return ""


# =============================================================================
# COMPONENT 4: Safety Check
# =============================================================================

BLOCKED_SHORTENERS = [
    'bit.ly', 'tinyurl', 't.co/', 'goo.gl', 'shorturl',
    'tiny.cc', 'is.gd', 'buff.ly', 'ow.ly', 'rebrand.ly'
]

TRUSTED_PROVIDERS = [
    'mailchimp.com', 'sendgrid.net', 'constantcontact.com', 'hubspot.com',
    'salesforce.com', 'amazonses.com', 'mailgun.com', 'sparkpost.com',
    'postmarkapp.com', 'sendinblue.com', 'klaviyo.com', 'campaign-archive.com',
    'list-manage.com', 'exacttarget.com', 'mktomail.com', 'pardot.com',
    'eloqua.com', 'responsys.net', 'blueshift.com', 'braze.com',
    'iterable.com', 'customer.io', 'intercom.io'
]


def check_link_safety(link: str) -> tuple[bool, str]:
    """
    Simulates Power Automate's Check_Link_Safety compose action.
    """
    if not link:
        return False, "No link provided"

    if len(link) < 10:
        return False, "Link too short"

    if not link.startswith('https://'):
        return False, f"Not HTTPS: {link[:50]}"

    link_lower = link.lower()
    for shortener in BLOCKED_SHORTENERS:
        if shortener in link_lower:
            return False, f"Blocked URL shortener: {shortener}"

    return True, "Basic safety checks passed"


def check_domain_match(link: str, sender_domain: str) -> tuple[bool, str]:
    """
    Simulates Power Automate's Check_Domain_Match compose action.
    """
    if not link:
        return False, "No link provided"

    link_lower = link.lower()

    # Check if sender domain is in the link
    if sender_domain and sender_domain in link_lower:
        return True, f"Domain matches sender: {sender_domain}"

    # Check trusted providers
    for provider in TRUSTED_PROVIDERS:
        if provider in link_lower:
            return True, f"Trusted provider: {provider}"

    return False, f"Domain mismatch - sender: {sender_domain}"


def is_safe_to_unsubscribe(link: str, sender_domain: str) -> tuple[bool, str]:
    """
    Combined safety check (both link safety AND domain match required).
    """
    safe, reason1 = check_link_safety(link)
    if not safe:
        return False, reason1

    matches, reason2 = check_domain_match(link, sender_domain)
    if not matches:
        return False, reason2

    return True, reason2


# =============================================================================
# COMPONENT 5: Main Flow Simulation
# =============================================================================

class EmailManagerFlow:
    """Simulates the main Power Automate flow."""

    def __init__(self):
        self.http_requests_made = []
        self.emails_moved = []
        self.emails_marked_read = []

    def process_email(self, email: Email) -> FlowResult:
        """Process a single email through the flow."""
        result = FlowResult(
            email_id=email.id,
            action=FlowAction.KEEP,
            is_promotional=False
        )

        # Step 1: Check if promotional
        result.is_promotional = detect_promotional(email.subject, email.body)

        if not result.is_promotional:
            result.action = FlowAction.KEEP
            return result

        # Step 2: Extract sender domain
        sender_domain = extract_sender_domain(email.from_address)

        # Step 3: Extract unsubscribe link
        result.unsubscribe_link = extract_unsubscribe_link(email.body)

        # Step 4: Check safety
        result.is_safe_to_unsubscribe, result.safety_reason = is_safe_to_unsubscribe(
            result.unsubscribe_link, sender_domain
        )

        # Step 5: Take action
        if result.is_safe_to_unsubscribe:
            result.action = FlowAction.UNSUBSCRIBE_AND_MOVE
            result.http_request_made = True
            result.http_request_url = result.unsubscribe_link
            self.http_requests_made.append(result.unsubscribe_link)
        else:
            result.action = FlowAction.MOVE_ONLY

        # Step 6: Move to folder
        result.moved_to_folder = "Promotional-ToDelete"
        self.emails_moved.append(email.id)
        self.emails_marked_read.append(email.id)

        return result


# =============================================================================
# COMPONENT 6: Weekly Purge Simulation
# =============================================================================

class WeeklyPurgeFlow:
    """Simulates the weekly purge Power Automate flow.

    Deletes ALL emails in the Promotional-ToDelete folder (no age limit).
    """

    def __init__(self):
        pass

    def process_folder(self, emails: list[Email]) -> PurgeResult:
        """Process all emails in the Promotional-ToDelete folder - delete ALL."""
        result = PurgeResult()

        for email in emails:
            if email.folder != "Promotional-ToDelete":
                continue

            # Delete ALL emails in the folder (no age check)
            result.deleted_emails.append({
                'id': email.id,
                'from': email.from_address,
                'subject': email.subject,
                'received': email.received_datetime.isoformat()
            })

        # Generate report
        result.report_generated = True
        result.report_content = self._generate_report(result)

        return result

    def _generate_report(self, result: PurgeResult) -> str:
        """Generate HTML report."""
        deleted_rows = ""
        for email in result.deleted_emails:
            deleted_rows += f"<tr><td>{html.escape(email['from'])}</td><td>{html.escape(email['subject'])}</td><td>{email['received']}</td></tr>\n"

        report = f"""
        <h2>Weekly Promotional Email Purge Report</h2>
        <h3>Summary</h3>
        <table border="1">
            <tr><td>Emails Deleted</td><td>{len(result.deleted_emails)}</td></tr>
        </table>
        <h3>Deleted Emails</h3>
        <table border="1">
            <tr><th>From</th><th>Subject</th><th>Received</th></tr>
            {deleted_rows if deleted_rows else "<tr><td colspan='3'>No emails in folder</td></tr>"}
        </table>
        """
        return report


# =============================================================================
# UNIT TESTS
# =============================================================================

class TestPromotionalDetection(unittest.TestCase):
    """Test Component 1: Promotional Detection"""

    def test_detects_offer_in_subject(self):
        self.assertTrue(detect_promotional("Special Offer Inside!", "Hello"))

    def test_detects_discount_in_subject(self):
        self.assertTrue(detect_promotional("50% Discount Today", "Hello"))

    def test_detects_sale_in_subject(self):
        self.assertTrue(detect_promotional("Flash Sale!", "Hello"))

    def test_detects_unsubscribe_in_body(self):
        self.assertTrue(detect_promotional("Newsletter", "Click to unsubscribe"))

    def test_detects_promotional_in_body(self):
        self.assertTrue(detect_promotional("News", "This is a promotional email"))

    def test_ignores_regular_email(self):
        self.assertFalse(detect_promotional("Meeting Tomorrow", "See you at 2pm"))

    def test_ignores_order_confirmation(self):
        self.assertFalse(detect_promotional("Your order has shipped", "Track your package"))

    def test_case_insensitive(self):
        self.assertTrue(detect_promotional("SPECIAL OFFER", "hello"))
        self.assertTrue(detect_promotional("special OFFER", "HELLO"))


class TestSenderDomainExtraction(unittest.TestCase):
    """Test Component 2: Sender Domain Extraction"""

    def test_simple_email(self):
        self.assertEqual(extract_sender_domain("user@example.com"), "example.com")

    def test_email_with_name(self):
        self.assertEqual(extract_sender_domain("John Doe <john@company.com>"), "company.com")

    def test_email_with_subdomain(self):
        self.assertEqual(extract_sender_domain("news@mail.company.com"), "mail.company.com")

    def test_no_at_symbol(self):
        self.assertEqual(extract_sender_domain("invalid-email"), "")

    def test_uppercase_domain(self):
        self.assertEqual(extract_sender_domain("user@EXAMPLE.COM"), "example.com")


class TestUnsubscribeLinkExtraction(unittest.TestCase):
    """Test Component 3: Unsubscribe Link Extraction"""

    def test_extracts_href_with_unsubscribe(self):
        body = '<a href="https://example.com/unsubscribe?id=123">Unsubscribe</a>'
        self.assertEqual(extract_unsubscribe_link(body), "https://example.com/unsubscribe?id=123")

    def test_extracts_from_complex_html(self):
        body = '''
        <html><body>
        <p>Thanks for reading!</p>
        <a href="https://company.com/preferences">Preferences</a>
        <a href="https://company.com/unsubscribe/abc">Unsubscribe</a>
        </body></html>
        '''
        link = extract_unsubscribe_link(body)
        self.assertIn("unsubscribe", link.lower())

    def test_returns_empty_for_no_unsubscribe(self):
        body = '<a href="https://example.com/home">Home</a>'
        self.assertEqual(extract_unsubscribe_link(body), "")

    def test_handles_single_quotes(self):
        body = "<a href='https://example.com/unsubscribe'>Unsub</a>"
        self.assertEqual(extract_unsubscribe_link(body), "https://example.com/unsubscribe")


class TestSafetyCheck(unittest.TestCase):
    """Test Component 4: Safety Check"""

    def test_https_passes(self):
        safe, _ = check_link_safety("https://example.com/unsubscribe")
        self.assertTrue(safe)

    def test_http_fails(self):
        safe, reason = check_link_safety("http://example.com/unsubscribe")
        self.assertFalse(safe)
        self.assertIn("HTTPS", reason)

    def test_bitly_fails(self):
        safe, reason = check_link_safety("https://bit.ly/abc123")
        self.assertFalse(safe)
        self.assertIn("shortener", reason.lower())

    def test_tinyurl_fails(self):
        safe, reason = check_link_safety("https://tinyurl.com/xyz")
        self.assertFalse(safe)

    def test_tco_fails(self):
        safe, reason = check_link_safety("https://t.co/abc123")
        self.assertFalse(safe)

    def test_empty_link_fails(self):
        safe, _ = check_link_safety("")
        self.assertFalse(safe)

    def test_domain_match_passes(self):
        matches, _ = check_domain_match("https://company.com/unsub", "company.com")
        self.assertTrue(matches)

    def test_domain_mismatch_fails(self):
        matches, _ = check_domain_match("https://other.com/unsub", "company.com")
        self.assertFalse(matches)

    def test_trusted_provider_passes(self):
        matches, reason = check_domain_match("https://list-manage.com/unsub", "company.com")
        self.assertTrue(matches)
        self.assertIn("Trusted", reason)

    def test_hubspot_passes(self):
        matches, _ = check_domain_match("https://email.hubspot.com/unsub", "retailer.com")
        self.assertTrue(matches)

    def test_mailchimp_passes(self):
        matches, _ = check_domain_match("https://mailchimp.com/unsub/abc", "newsletter.org")
        self.assertTrue(matches)


class TestMainFlow(unittest.TestCase):
    """Test Component 5: Main Flow Integration"""

    def setUp(self):
        self.flow = EmailManagerFlow()

    def test_keeps_regular_email(self):
        email = Email(
            id="1",
            from_address="john@company.com",
            subject="Meeting Tomorrow",
            body="See you at 2pm",
            received_datetime=datetime.now()
        )
        result = self.flow.process_email(email)
        self.assertEqual(result.action, FlowAction.KEEP)
        self.assertFalse(result.is_promotional)

    def test_unsubscribes_safe_promotional(self):
        email = Email(
            id="2",
            from_address="news@company.com",
            subject="Special Offer!",
            body='<a href="https://company.com/unsubscribe">Unsubscribe</a>',
            received_datetime=datetime.now()
        )
        result = self.flow.process_email(email)
        self.assertEqual(result.action, FlowAction.UNSUBSCRIBE_AND_MOVE)
        self.assertTrue(result.is_safe_to_unsubscribe)
        self.assertTrue(result.http_request_made)

    def test_moves_only_unsafe_promotional(self):
        email = Email(
            id="3",
            from_address="spam@sender.com",
            subject="Act Now!",
            body='<a href="https://bit.ly/abc">Unsubscribe</a>',
            received_datetime=datetime.now()
        )
        result = self.flow.process_email(email)
        self.assertEqual(result.action, FlowAction.MOVE_ONLY)
        self.assertFalse(result.is_safe_to_unsubscribe)
        self.assertFalse(result.http_request_made)

    def test_moves_domain_mismatch(self):
        email = Email(
            id="4",
            from_address="news@company.com",
            subject="Free Gift!",
            body='<a href="https://suspicious-site.com/unsubscribe">Unsubscribe</a>',
            received_datetime=datetime.now()
        )
        result = self.flow.process_email(email)
        self.assertEqual(result.action, FlowAction.MOVE_ONLY)
        self.assertIn("mismatch", result.safety_reason.lower())


class TestWeeklyPurge(unittest.TestCase):
    """Test Component 6: Weekly Purge - Deletes ALL emails in folder"""

    def setUp(self):
        self.purge = WeeklyPurgeFlow()

    def test_deletes_old_emails(self):
        """Old emails should be deleted."""
        emails = [
            Email(
                id="1",
                from_address="old@example.com",
                subject="Old promo",
                body="test",
                received_datetime=datetime.now() - timedelta(days=10),
                folder="Promotional-ToDelete"
            )
        ]
        result = self.purge.process_folder(emails)
        self.assertEqual(len(result.deleted_emails), 1)

    def test_deletes_recent_emails_too(self):
        """Recent emails should ALSO be deleted (no age limit)."""
        emails = [
            Email(
                id="2",
                from_address="new@example.com",
                subject="Recent promo",
                body="test",
                received_datetime=datetime.now() - timedelta(hours=1),  # 1 hour old
                folder="Promotional-ToDelete"
            )
        ]
        result = self.purge.process_folder(emails)
        self.assertEqual(len(result.deleted_emails), 1)  # Should delete!

    def test_ignores_other_folders(self):
        """Only deletes from Promotional-ToDelete folder."""
        emails = [
            Email(
                id="3",
                from_address="inbox@example.com",
                subject="Inbox email",
                body="test",
                received_datetime=datetime.now() - timedelta(days=10),
                folder="Inbox"
            )
        ]
        result = self.purge.process_folder(emails)
        self.assertEqual(len(result.deleted_emails), 0)

    def test_deletes_all_emails_in_folder(self):
        """Should delete ALL emails regardless of age."""
        emails = [
            Email(
                id="1",
                from_address="old@example.com",
                subject="10 days old",
                body="test",
                received_datetime=datetime.now() - timedelta(days=10),
                folder="Promotional-ToDelete"
            ),
            Email(
                id="2",
                from_address="recent@example.com",
                subject="1 day old",
                body="test",
                received_datetime=datetime.now() - timedelta(days=1),
                folder="Promotional-ToDelete"
            ),
            Email(
                id="3",
                from_address="new@example.com",
                subject="1 hour old",
                body="test",
                received_datetime=datetime.now() - timedelta(hours=1),
                folder="Promotional-ToDelete"
            ),
        ]
        result = self.purge.process_folder(emails)
        self.assertEqual(len(result.deleted_emails), 3)  # ALL deleted

    def test_generates_report(self):
        """Report should list all deleted emails."""
        emails = [
            Email(
                id="1",
                from_address="promo@example.com",
                subject="Deleted promo",
                body="test",
                received_datetime=datetime.now() - timedelta(days=1),
                folder="Promotional-ToDelete"
            )
        ]
        result = self.purge.process_folder(emails)
        self.assertTrue(result.report_generated)
        self.assertIn("Deleted", result.report_content)
        self.assertIn("promo@example.com", result.report_content)


if __name__ == '__main__':
    print("=" * 70)
    print("POWER AUTOMATE EMAIL MANAGER - SANDBOX UNIT TESTS")
    print("=" * 70)

    # Run tests with verbosity
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes in order
    suite.addTests(loader.loadTestsFromTestCase(TestPromotionalDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestSenderDomainExtraction))
    suite.addTests(loader.loadTestsFromTestCase(TestUnsubscribeLinkExtraction))
    suite.addTests(loader.loadTestsFromTestCase(TestSafetyCheck))
    suite.addTests(loader.loadTestsFromTestCase(TestMainFlow))
    suite.addTests(loader.loadTestsFromTestCase(TestWeeklyPurge))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    print(f"TESTS RUN: {result.testsRun}")
    print(f"FAILURES: {len(result.failures)}")
    print(f"ERRORS: {len(result.errors)}")
    print("=" * 70)
