#!/usr/bin/env python3
"""
End-to-End Flow Simulation for Power Automate Email Manager

Target Account: albert.greenberg@hotmail.com (Outlook.com)

This simulates a realistic week of email processing through both flows.
"""

import json
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import random


# =============================================================================
# Configuration
# =============================================================================

CONFIG = {
    "account_email": "albert.greenberg@hotmail.com",
    "account_type": "outlook.com",  # Personal Microsoft account
    "promotional_folder": "Promotional-ToDelete",
    "purge_schedule": "Sunday 3:00 AM PST",
    "purge_behavior": "Delete ALL emails in folder (no age limit)"
}


# =============================================================================
# Import components from sandbox
# =============================================================================

class FlowAction(Enum):
    KEEP = "keep"
    MOVE_ONLY = "move_to_promotional"
    UNSUBSCRIBE_AND_MOVE = "unsubscribe_and_move"


PROMOTIONAL_KEYWORDS_SUBJECT = [
    'offer', 'discount', 'sale', 'deal', 'limited time',
    'act now', 'exclusive', 'free', 'promotion'
]

PROMOTIONAL_KEYWORDS_BODY = [
    'unsubscribe', 'promotional', 'marketing email', 'email preferences'
]

BLOCKED_SHORTENERS = [
    'bit.ly', 'tinyurl', 't.co/', 'goo.gl', 'shorturl',
    'tiny.cc', 'is.gd', 'buff.ly', 'ow.ly', 'rebrand.ly'
]

TRUSTED_PROVIDERS = [
    'mailchimp.com', 'sendgrid.net', 'constantcontact.com', 'hubspot.com',
    'salesforce.com', 'amazonses.com', 'mailgun.com', 'sparkpost.com',
    'list-manage.com', 'campaign-archive.com', 'klaviyo.com'
]


@dataclass
class Email:
    id: str
    from_address: str
    subject: str
    body: str
    received_datetime: datetime
    folder: str = "Inbox"


@dataclass
class FlowResult:
    email_id: str
    action: FlowAction
    is_promotional: bool
    unsubscribe_link: Optional[str] = None
    is_safe_to_unsubscribe: bool = False
    safety_reason: Optional[str] = None


# =============================================================================
# Realistic Test Email Dataset
# =============================================================================

def generate_test_emails() -> list[Email]:
    """Generate a realistic week of emails."""
    now = datetime.now()

    emails = [
        # --- LEGITIMATE EMAILS (should KEEP) ---
        Email(
            id="e001",
            from_address="boss@company.com",
            subject="Q1 Review Meeting",
            body="Hi, let's meet tomorrow at 2pm to discuss Q1 results. Best, Boss",
            received_datetime=now - timedelta(hours=2),
        ),
        Email(
            id="e002",
            from_address="noreply@amazon.com",
            subject="Your order has shipped",
            body="Your order #123-456 is on its way. Track at amazon.com/track",
            received_datetime=now - timedelta(hours=5),
        ),
        Email(
            id="e003",
            from_address="friend@gmail.com",
            subject="Dinner Saturday?",
            body="Hey! Want to grab dinner this Saturday? Let me know!",
            received_datetime=now - timedelta(days=1),
        ),
        Email(
            id="e004",
            from_address="alerts@bank.com",
            subject="Your statement is ready",
            body="Your monthly statement is now available. Log in to view.",
            received_datetime=now - timedelta(days=2),
        ),
        Email(
            id="e005",
            from_address="noreply@github.com",
            subject="[repo] New pull request",
            body="A new pull request was opened in your repository.",
            received_datetime=now - timedelta(days=1),
        ),

        # --- PROMOTIONAL - SAFE TO UNSUBSCRIBE ---
        Email(
            id="p001",
            from_address="deals@bestbuy.com",
            subject="50% OFF Electronics Sale!",
            body='''
            <html>
            <p>Don't miss our biggest sale of the year!</p>
            <p>50% off all electronics this weekend only.</p>
            <a href="https://bestbuy.com/unsubscribe?id=abc123">Unsubscribe</a>
            </html>
            ''',
            received_datetime=now - timedelta(hours=3),
        ),
        Email(
            id="p002",
            from_address="news@techcrunch.com",
            subject="Your Weekly Tech Digest",
            body='''
            <html>
            <p>This week in tech...</p>
            <p>To stop receiving emails:
            <a href="https://list-manage.com/unsubscribe/techcrunch/xyz">unsubscribe</a></p>
            </html>
            ''',
            received_datetime=now - timedelta(days=1),
        ),
        Email(
            id="p003",
            from_address="marketing@hubspot.com",
            subject="Free Marketing Webinar",
            body='''
            <p>Join our free webinar on growth hacking!</p>
            <a href="https://email.hubspot.com/unsubscribe/abc">Unsubscribe from marketing emails</a>
            ''',
            received_datetime=now - timedelta(days=2),
        ),
        Email(
            id="p004",
            from_address="newsletter@medium.com",
            subject="Exclusive stories for you",
            body='''
            <p>Based on your reading history...</p>
            <a href="https://medium.com/unsubscribe/daily-digest">Unsubscribe</a>
            ''',
            received_datetime=now - timedelta(days=3),
        ),
        Email(
            id="p005",
            from_address="promo@retailer.com",
            subject="Limited Time Deal - Act Now!",
            body='''
            <p>Use code SAVE20 for 20% off!</p>
            <a href="https://mailchimp.com/unsubscribe/retailer/123">Unsubscribe</a>
            ''',
            received_datetime=now - timedelta(days=4),
        ),

        # --- PROMOTIONAL - UNSAFE (should move but NOT unsubscribe) ---
        Email(
            id="u001",
            from_address="deals@sketchy-store.xyz",
            subject="You won a FREE iPhone!!!",
            body='''
            <p>CONGRATULATIONS! Click here to claim!</p>
            <a href="https://bit.ly/free-iphone">Unsubscribe</a>
            ''',
            received_datetime=now - timedelta(hours=6),
        ),
        Email(
            id="u002",
            from_address="marketing@legit-company.com",
            subject="Special Offer Inside",
            body='''
            <p>Check out our new products!</p>
            <a href="https://totally-different-domain.com/unsubscribe">Unsubscribe</a>
            ''',
            received_datetime=now - timedelta(days=1),
        ),
        Email(
            id="u003",
            from_address="newsletter@news-site.com",
            subject="Breaking: Exclusive discount",
            body='''
            <p>Limited time offer!</p>
            <a href="http://insecure-link.com/unsubscribe">Unsubscribe</a>
            ''',
            received_datetime=now - timedelta(days=2),
        ),
        Email(
            id="u004",
            from_address="promo@shop.com",
            subject="Deal of the Day",
            body='''
            <p>Today only - 70% off!</p>
            <a href="https://t.co/abc123">Click to unsubscribe</a>
            ''',
            received_datetime=now - timedelta(days=1),
        ),
        Email(
            id="u005",
            from_address="spam@unknown.net",
            subject="Act now - limited time",
            body='''
            <p>This promotional email has great deals!</p>
            <!-- No unsubscribe link at all -->
            ''',
            received_datetime=now - timedelta(days=3),
        ),

        # --- OLD PROMOTIONAL (in folder, ready for purge) ---
        Email(
            id="old001",
            from_address="old-promo@store.com",
            subject="Old sale from 10 days ago",
            body="<a href='https://store.com/unsub'>Unsubscribe</a>",
            received_datetime=now - timedelta(days=10),
            folder="Promotional-ToDelete"
        ),
        Email(
            id="old002",
            from_address="old-news@newsletter.com",
            subject="Newsletter from 2 weeks ago",
            body="<a href='https://newsletter.com/unsub'>Unsubscribe</a>",
            received_datetime=now - timedelta(days=14),
            folder="Promotional-ToDelete"
        ),
        Email(
            id="old003",
            from_address="recent-promo@shop.com",
            subject="Recent promo from 3 days ago",
            body="<a href='https://shop.com/unsub'>Unsubscribe</a>",
            received_datetime=now - timedelta(days=3),
            folder="Promotional-ToDelete"
        ),
    ]

    return emails


# =============================================================================
# Flow Logic (simplified from sandbox)
# =============================================================================

def detect_promotional(subject: str, body: str) -> bool:
    subject_lower = subject.lower()
    body_lower = body.lower()

    for kw in PROMOTIONAL_KEYWORDS_SUBJECT:
        if kw in subject_lower:
            return True
    for kw in PROMOTIONAL_KEYWORDS_BODY:
        if kw in body_lower:
            return True
    return False


def extract_sender_domain(from_addr: str) -> str:
    if '@' not in from_addr:
        return ""
    return from_addr.split('@')[-1].replace('>', '').strip().lower()


def extract_unsubscribe_link(body: str) -> str:
    import re
    pattern = r'href=["\']([^"\']*unsubscribe[^"\']*)["\']'
    matches = re.findall(pattern, body, re.IGNORECASE)
    for m in matches:
        if m.startswith('http'):
            return m
    return matches[0] if matches else ""


def is_safe_to_unsubscribe(link: str, sender_domain: str) -> tuple[bool, str]:
    if not link:
        return False, "No unsubscribe link"
    if not link.startswith('https://'):
        return False, "Not HTTPS"

    link_lower = link.lower()
    for shortener in BLOCKED_SHORTENERS:
        if shortener in link_lower:
            return False, f"URL shortener: {shortener}"

    if sender_domain and sender_domain in link_lower:
        return True, f"Domain match: {sender_domain}"

    for provider in TRUSTED_PROVIDERS:
        if provider in link_lower:
            return True, f"Trusted: {provider}"

    return False, "Domain mismatch"


def process_email(email: Email) -> FlowResult:
    result = FlowResult(
        email_id=email.id,
        action=FlowAction.KEEP,
        is_promotional=False
    )

    result.is_promotional = detect_promotional(email.subject, email.body)

    if not result.is_promotional:
        return result

    sender_domain = extract_sender_domain(email.from_address)
    result.unsubscribe_link = extract_unsubscribe_link(email.body)
    result.is_safe_to_unsubscribe, result.safety_reason = is_safe_to_unsubscribe(
        result.unsubscribe_link, sender_domain
    )

    if result.is_safe_to_unsubscribe:
        result.action = FlowAction.UNSUBSCRIBE_AND_MOVE
    else:
        result.action = FlowAction.MOVE_ONLY

    return result


# =============================================================================
# End-to-End Simulation
# =============================================================================

def run_e2e_simulation():
    print("=" * 80)
    print("END-TO-END FLOW SIMULATION")
    print("=" * 80)
    print(f"\nAccount: {CONFIG['account_email']}")
    print(f"Account Type: {CONFIG['account_type']}")
    print(f"Promotional Folder: {CONFIG['promotional_folder']}")
    print(f"Purge Schedule: {CONFIG['purge_schedule']}")
    print()

    emails = generate_test_emails()
    inbox_emails = [e for e in emails if e.folder == "Inbox"]
    folder_emails = [e for e in emails if e.folder == "Promotional-ToDelete"]

    print("=" * 80)
    print("PHASE 1: MAIN FLOW - Processing Incoming Emails")
    print("=" * 80)
    print(f"\nProcessing {len(inbox_emails)} emails from Inbox...\n")

    stats = {
        'kept': [],
        'safe_unsubscribe': [],
        'unsafe_move_only': []
    }

    for email in inbox_emails:
        result = process_email(email)

        action_icon = {
            FlowAction.KEEP: "✓ KEEP",
            FlowAction.MOVE_ONLY: "⚠ MOVE (no unsub)",
            FlowAction.UNSUBSCRIBE_AND_MOVE: "🔓 UNSUB + MOVE"
        }[result.action]

        print(f"[{email.id}] {action_icon}")
        print(f"    From: {email.from_address}")
        print(f"    Subject: {email.subject[:50]}...")

        if result.is_promotional:
            print(f"    Unsubscribe Link: {result.unsubscribe_link[:60] if result.unsubscribe_link else 'None'}...")
            print(f"    Safe: {result.is_safe_to_unsubscribe} ({result.safety_reason})")
        print()

        if result.action == FlowAction.KEEP:
            stats['kept'].append(email)
        elif result.action == FlowAction.UNSUBSCRIBE_AND_MOVE:
            stats['safe_unsubscribe'].append(email)
        else:
            stats['unsafe_move_only'].append(email)

    print("-" * 80)
    print("PHASE 1 SUMMARY")
    print("-" * 80)
    print(f"  Kept (not promotional):     {len(stats['kept'])}")
    print(f"  Unsubscribed + Moved:       {len(stats['safe_unsubscribe'])}")
    print(f"  Moved Only (unsafe link):   {len(stats['unsafe_move_only'])}")
    print(f"  Total Processed:            {len(inbox_emails)}")

    # Simulate moving emails to folder
    for email in stats['safe_unsubscribe'] + stats['unsafe_move_only']:
        email.folder = "Promotional-ToDelete"
        folder_emails.append(email)

    print("\n")
    print("=" * 80)
    print("PHASE 2: WEEKLY PURGE - Delete ALL Emails in Promotional Folder")
    print("=" * 80)

    print(f"\nBehavior: {CONFIG['purge_behavior']}")
    print(f"Emails in {CONFIG['promotional_folder']}: {len(folder_emails)}\n")

    deleted = []

    for email in folder_emails:
        age_days = (datetime.now() - email.received_datetime).days
        deleted.append(email)
        print(f"[{email.id}] 🗑️ DELETE (age: {age_days} days)")
        print(f"    From: {email.from_address}")
        print(f"    Subject: {email.subject[:50]}...")
        print()

    print("-" * 80)
    print("PHASE 2 SUMMARY")
    print("-" * 80)
    print(f"  Emails Deleted:  {len(deleted)} (ALL emails in folder)")

    print("\n")
    print("=" * 80)
    print("WEEKLY REPORT EMAIL")
    print("=" * 80)
    print(f"\nTo: {CONFIG['account_email']}")
    print(f"Subject: Weekly Email Purge Report - {datetime.now().strftime('%Y-%m-%d')} | {len(deleted)} deleted")
    print()
    print("--- Report Body ---")
    print(f"Emails Deleted: {len(deleted)}")
    print()
    if deleted:
        print("Deleted Emails:")
        print("-" * 60)
        print(f"{'From':<30} {'Subject':<30}")
        print("-" * 60)
        for e in deleted:
            print(f"{e.from_address[:28]:<30} {e.subject[:28]:<30}")
    print()

    print("=" * 80)
    print("END-TO-END SIMULATION COMPLETE")
    print("=" * 80)

    # Validation
    print("\n")
    print("=" * 80)
    print("VALIDATION CHECKS")
    print("=" * 80)

    checks = [
        ("Legitimate emails kept", len(stats['kept']) == 5, f"Expected 5, got {len(stats['kept'])}"),
        ("Safe promotional unsubscribed", len(stats['safe_unsubscribe']) == 5, f"Expected 5, got {len(stats['safe_unsubscribe'])}"),
        ("Unsafe promotional moved only", len(stats['unsafe_move_only']) == 5, f"Expected 5, got {len(stats['unsafe_move_only'])}"),
        ("All folder emails deleted", len(deleted) == len(folder_emails), f"Expected {len(folder_emails)}, got {len(deleted)}"),
    ]

    all_passed = True
    for name, passed, detail in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
        if not passed:
            print(f"       {detail}")
            all_passed = False

    print()
    if all_passed:
        print("🎉 ALL VALIDATION CHECKS PASSED")
    else:
        print("⚠️  SOME CHECKS FAILED - Review above")

    return all_passed


if __name__ == '__main__':
    success = run_e2e_simulation()
    exit(0 if success else 1)
