#!/usr/bin/env python3
"""
Test script to validate Power Automate flow logic locally.
This simulates the detection and safety check logic before deploying to Power Automate.
"""

import re
from urllib.parse import urlparse

# Promotional keywords (from flow)
PROMOTIONAL_KEYWORDS_SUBJECT = [
    'offer', 'discount', 'sale', 'deal', 'limited time',
    'act now', 'exclusive', 'free', 'promotion'
]

PROMOTIONAL_KEYWORDS_BODY = [
    'unsubscribe', 'promotional', 'marketing email', 'email preferences'
]

# Blocked URL shorteners
BLOCKED_SHORTENERS = [
    'bit.ly', 'tinyurl', 't.co/', 'goo.gl', 'shorturl',
    'tiny.cc', 'is.gd', 'buff.ly', 'ow.ly', 'rebrand.ly'
]

# Trusted email service providers
TRUSTED_PROVIDERS = [
    'mailchimp.com', 'sendgrid.net', 'constantcontact.com', 'hubspot.com',
    'salesforce.com', 'amazonses.com', 'mailgun.com', 'sparkpost.com',
    'postmarkapp.com', 'sendinblue.com', 'klaviyo.com', 'campaign-archive.com',
    'list-manage.com', 'exacttarget.com', 'mktomail.com', 'pardot.com',
    'eloqua.com', 'responsys.net', 'blueshift.com', 'braze.com',
    'iterable.com', 'customer.io', 'intercom.io'
]


def is_promotional(subject: str, body: str) -> bool:
    """Check if email is promotional based on keywords."""
    subject_lower = subject.lower()
    body_lower = body.lower()

    for keyword in PROMOTIONAL_KEYWORDS_SUBJECT:
        if keyword in subject_lower:
            return True

    for keyword in PROMOTIONAL_KEYWORDS_BODY:
        if keyword in body_lower:
            return True

    return False


def extract_unsubscribe_link(body: str) -> str:
    """Extract unsubscribe link from email body."""
    # Look for href containing "unsubscribe"
    pattern = r'href=["\']([^"\']*unsubscribe[^"\']*)["\']'
    matches = re.findall(pattern, body, re.IGNORECASE)

    if matches:
        return matches[0]

    # Fallback: look for any URL near "unsubscribe" text
    if 'unsubscribe' in body.lower():
        url_pattern = r'https?://[^\s<>"\']+unsubscribe[^\s<>"\']*'
        url_matches = re.findall(url_pattern, body, re.IGNORECASE)
        if url_matches:
            return url_matches[0]

    return ""


def extract_sender_domain(from_address: str) -> str:
    """Extract domain from sender email address."""
    if '@' in from_address:
        domain = from_address.split('@')[-1]
        # Clean up any trailing > or spaces
        domain = domain.replace('>', '').replace(' ', '').strip()
        return domain.lower()
    return ""


def is_safe_to_unsubscribe(link: str, sender_domain: str) -> tuple[bool, str]:
    """
    Check if unsubscribe link is safe to click.
    Returns (is_safe, reason)
    """
    if not link:
        return False, "No unsubscribe link found"

    # Must be HTTPS
    if not link.startswith('https://'):
        return False, f"Link is not HTTPS: {link[:50]}..."

    # Check for URL shorteners
    for shortener in BLOCKED_SHORTENERS:
        if shortener in link.lower():
            return False, f"Link uses URL shortener: {shortener}"

    # Check domain matches sender OR is trusted provider
    link_lower = link.lower()

    if sender_domain and sender_domain in link_lower:
        return True, f"Domain matches sender: {sender_domain}"

    for provider in TRUSTED_PROVIDERS:
        if provider in link_lower:
            return True, f"Link uses trusted provider: {provider}"

    return False, f"Domain mismatch - sender: {sender_domain}, link domain doesn't match"


def test_email(subject: str, body: str, from_address: str) -> dict:
    """Test an email through the flow logic."""
    result = {
        'from': from_address,
        'subject': subject[:50] + '...' if len(subject) > 50 else subject,
        'is_promotional': False,
        'unsubscribe_link': None,
        'is_safe_to_unsubscribe': False,
        'safety_reason': None,
        'action': 'KEEP'
    }

    result['is_promotional'] = is_promotional(subject, body)

    if result['is_promotional']:
        sender_domain = extract_sender_domain(from_address)
        result['sender_domain'] = sender_domain

        link = extract_unsubscribe_link(body)
        result['unsubscribe_link'] = link[:80] + '...' if len(link) > 80 else link

        is_safe, reason = is_safe_to_unsubscribe(link, sender_domain)
        result['is_safe_to_unsubscribe'] = is_safe
        result['safety_reason'] = reason

        if is_safe:
            result['action'] = 'UNSUBSCRIBE + MOVE TO PROMOTIONAL FOLDER'
        else:
            result['action'] = 'MOVE TO PROMOTIONAL FOLDER (no unsubscribe)'

    return result


def print_result(result: dict):
    """Pretty print test result."""
    print("\n" + "="*70)
    print(f"From: {result['from']}")
    print(f"Subject: {result['subject']}")
    print("-"*70)
    print(f"Is Promotional: {result['is_promotional']}")
    if result['is_promotional']:
        print(f"Sender Domain: {result.get('sender_domain', 'N/A')}")
        print(f"Unsubscribe Link: {result['unsubscribe_link'] or 'None found'}")
        print(f"Safe to Unsubscribe: {result['is_safe_to_unsubscribe']}")
        print(f"Safety Reason: {result['safety_reason']}")
    print(f"\n>>> ACTION: {result['action']}")
    print("="*70)


# Test cases
TEST_EMAILS = [
    {
        'subject': '50% OFF - Limited Time Offer!',
        'body': '''
            Don't miss this amazing deal!
            Get 50% off everything in our store.
            <a href="https://company.com/unsubscribe?id=123">Unsubscribe</a>
        ''',
        'from': 'deals@company.com'
    },
    {
        'subject': 'Your weekly newsletter',
        'body': '''
            Here's what's happening this week...
            To unsubscribe, click here: https://list-manage.com/unsubscribe/abc123
        ''',
        'from': 'newsletter@example.com'
    },
    {
        'subject': 'URGENT: Act Now!!!',
        'body': '''
            Click this suspicious link!
            <a href="https://bit.ly/3xyzABC">Unsubscribe</a>
        ''',
        'from': 'spam@suspicious-domain.xyz'
    },
    {
        'subject': 'Meeting reminder',
        'body': '''
            Don't forget about our meeting tomorrow at 2pm.
            Best regards,
            John
        ''',
        'from': 'john@company.com'
    },
    {
        'subject': 'New products just for you!',
        'body': '''
            Check out our new arrivals.
            <a href="https://totally-different-domain.com/unsubscribe">Unsubscribe</a>
        ''',
        'from': 'marketing@retailer.com'
    },
    {
        'subject': 'Exclusive discount inside',
        'body': '''
            Use code SAVE20 for 20% off.
            <a href="https://email.hubspot.com/unsubscribe/retailer">Unsubscribe</a>
        ''',
        'from': 'promo@retailer.com'
    },
    {
        'subject': 'Your order has shipped',
        'body': '''
            Your order #12345 is on its way!
            Track your package here.
        ''',
        'from': 'orders@amazon.com'
    },
    {
        'subject': 'Free webinar invitation',
        'body': '''
            Join us for a free webinar on productivity.
            http://insecure-link.com/unsubscribe
        ''',
        'from': 'webinars@company.com'
    },
]


if __name__ == '__main__':
    print("\n" + "#"*70)
    print("# POWER AUTOMATE FLOW LOGIC TEST")
    print("# Testing email detection and unsubscribe safety checks")
    print("#"*70)

    stats = {
        'total': len(TEST_EMAILS),
        'promotional': 0,
        'safe_unsubscribe': 0,
        'unsafe_unsubscribe': 0,
        'not_promotional': 0
    }

    for email in TEST_EMAILS:
        result = test_email(email['subject'], email['body'], email['from'])
        print_result(result)

        if result['is_promotional']:
            stats['promotional'] += 1
            if result['is_safe_to_unsubscribe']:
                stats['safe_unsubscribe'] += 1
            else:
                stats['unsafe_unsubscribe'] += 1
        else:
            stats['not_promotional'] += 1

    print("\n" + "#"*70)
    print("# SUMMARY")
    print("#"*70)
    print(f"Total emails tested: {stats['total']}")
    print(f"Promotional: {stats['promotional']}")
    print(f"  - Safe to unsubscribe: {stats['safe_unsubscribe']}")
    print(f"  - Unsafe (skip unsubscribe): {stats['unsafe_unsubscribe']}")
    print(f"Not promotional (keep): {stats['not_promotional']}")
    print("#"*70)
    print("\nAll tests completed successfully!")
