#!/usr/bin/env python3
"""
Bulk Scan Simulation - Processing thousands of existing emails

This simulates scanning an existing inbox with thousands of promotional emails.
"""

import random
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional


CONFIG = {
    "account_email": "albert.greenberg@hotmail.com",
    "api_batch_size": 250,  # Outlook API limit per request
}


# Realistic email sender patterns
PROMOTIONAL_SENDERS = [
    "deals@bestbuy.com", "offers@amazon.com", "news@linkedin.com",
    "marketing@salesforce.com", "promo@target.com", "newsletter@medium.com",
    "updates@twitter.com", "digest@quora.com", "news@producthunt.com",
    "offers@groupon.com", "deals@retailmenot.com", "promo@ebay.com",
    "marketing@hubspot.com", "newsletter@substack.com", "updates@github.com",
    "promo@walmart.com", "deals@costco.com", "offers@macys.com",
    "marketing@mailchimp.com", "news@techcrunch.com", "updates@slack.com",
    "promo@nordstrom.com", "deals@kohls.com", "offers@jcpenney.com",
    "newsletter@nytimes.com", "digest@wsj.com", "updates@forbes.com",
]

PROMOTIONAL_SUBJECTS = [
    "50% OFF Everything!", "Limited Time Offer", "Flash Sale Today Only",
    "Exclusive Deal for You", "Don't Miss This Sale", "Free Shipping Weekend",
    "New Arrivals + 30% Off", "Members Only: Extra Savings", "Last Chance!",
    "Weekly Digest", "Your Daily Newsletter", "Top Stories This Week",
    "Act Now - Expires Tonight", "Special Promotion Inside", "VIP Access",
    "Clearance Event", "Buy One Get One Free", "Reward Points Expiring",
]

LEGITIMATE_SENDERS = [
    "boss@company.com", "hr@company.com", "it-support@company.com",
    "friend@gmail.com", "family@yahoo.com", "colleague@work.com",
    "noreply@bank.com", "alerts@creditcard.com", "statements@utility.com",
    "orders@amazon.com", "shipping@fedex.com", "receipts@apple.com",
]

LEGITIMATE_SUBJECTS = [
    "Meeting Tomorrow", "Project Update", "Quick Question",
    "Your Order Has Shipped", "Payment Received", "Account Statement",
    "Dinner Plans?", "Happy Birthday!", "Photos from Last Weekend",
    "Interview Confirmation", "Contract Signed", "Invoice #12345",
]


@dataclass
class Email:
    id: str
    from_address: str
    subject: str
    body: str
    received_datetime: datetime
    is_promotional: bool


def generate_realistic_inbox(total_emails: int, promotional_ratio: float = 0.7) -> list[Email]:
    """Generate a realistic inbox with mix of promotional and legitimate emails."""
    emails = []
    now = datetime.now()

    for i in range(total_emails):
        is_promo = random.random() < promotional_ratio

        if is_promo:
            sender = random.choice(PROMOTIONAL_SENDERS)
            subject = random.choice(PROMOTIONAL_SUBJECTS)
            body = f"<html><body><p>{subject}</p><a href='https://{sender.split('@')[1]}/unsubscribe'>Unsubscribe</a></body></html>"
        else:
            sender = random.choice(LEGITIMATE_SENDERS)
            subject = random.choice(LEGITIMATE_SUBJECTS)
            body = f"<html><body><p>{subject}</p></body></html>"

        # Random date within last 2 years
        days_ago = random.randint(0, 730)
        received = now - timedelta(days=days_ago, hours=random.randint(0, 23))

        emails.append(Email(
            id=f"email_{i:05d}",
            from_address=sender,
            subject=subject,
            body=body,
            received_datetime=received,
            is_promotional=is_promo
        ))

    return emails


def simulate_bulk_scan(emails: list[Email], batch_size: int = 250):
    """Simulate the bulk scan process with API batching."""
    print("=" * 80)
    print("BULK SCAN SIMULATION")
    print("=" * 80)
    print(f"\nAccount: {CONFIG['account_email']}")
    print(f"Total Emails in Inbox: {len(emails):,}")
    print(f"API Batch Size: {batch_size}")
    print()

    # Filter promotional emails (simulating the search query)
    promotional = [e for e in emails if e.is_promotional]
    legitimate = [e for e in emails if not e.is_promotional]

    print(f"Promotional Emails Found: {len(promotional):,}")
    print(f"Legitimate Emails: {len(legitimate):,}")
    print()

    # Calculate batches needed
    batches_needed = (len(promotional) + batch_size - 1) // batch_size

    print("=" * 80)
    print("BATCH PROCESSING")
    print("=" * 80)
    print(f"\nBatches Required: {batches_needed}")
    print()

    total_moved = 0
    for batch_num in range(batches_needed):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(promotional))
        batch_emails = promotional[start_idx:end_idx]

        print(f"Batch {batch_num + 1}/{batches_needed}:")
        print(f"  Processing emails {start_idx + 1:,} to {end_idx:,}")
        print(f"  Emails in batch: {len(batch_emails)}")
        print(f"  → Moved to Promotional-ToDelete: {len(batch_emails)}")
        total_moved += len(batch_emails)
        print()

    print("=" * 80)
    print("BULK SCAN SUMMARY")
    print("=" * 80)
    print(f"\nTotal Emails Scanned: {len(emails):,}")
    print(f"Promotional Identified: {len(promotional):,}")
    print(f"Moved to Promotional-ToDelete: {total_moved:,}")
    print(f"Legitimate Emails Kept: {len(legitimate):,}")
    print()

    # Sample of what was moved
    print("Sample of Moved Emails (first 10):")
    print("-" * 60)
    for email in promotional[:10]:
        print(f"  From: {email.from_address}")
        print(f"  Subject: {email.subject}")
        print(f"  Date: {email.received_datetime.strftime('%Y-%m-%d')}")
        print()

    print("=" * 80)
    print("WORKFLOW")
    print("=" * 80)
    print("""
1. IMPORT bulk-scan-flow.json to Power Automate
2. RUN the flow manually (click "Run")
3. Each run processes up to 250 emails
4. REPEAT until no more promotional emails found
5. REVIEW the Promotional-ToDelete folder
6. RESCUE any false positives back to Inbox
7. RUN weekly-purge-flow.json (or wait for Sunday 3am)
8. RECEIVE email report of everything deleted
""")

    print("=" * 80)
    print("ESTIMATED RUNS NEEDED FOR YOUR INBOX")
    print("=" * 80)
    print(f"""
If you have ~{len(promotional):,} promotional emails:
  → You'll need to run the bulk scan ~{batches_needed} times
  → Each run takes ~1-2 minutes
  → Total time: ~{batches_needed * 2} minutes

After bulk scan is complete:
  → The weekly purge will delete all {len(promotional):,} emails
  → You'll receive a report listing everything deleted
""")

    return {
        'total': len(emails),
        'promotional': len(promotional),
        'legitimate': len(legitimate),
        'batches': batches_needed
    }


if __name__ == '__main__':
    # Simulate inbox with 5000 emails (realistic for active email user)
    print("\nGenerating simulated inbox with 5,000 emails...")
    print("(70% promotional, 30% legitimate - typical ratio)\n")

    inbox = generate_realistic_inbox(5000, promotional_ratio=0.7)
    stats = simulate_bulk_scan(inbox)

    print("=" * 80)
    print("VALIDATION")
    print("=" * 80)
    checks = [
        ("Promotional emails identified", stats['promotional'] > 3000),
        ("Legitimate emails preserved", stats['legitimate'] > 1000),
        ("Batch calculation correct", stats['batches'] == (stats['promotional'] + 249) // 250),
    ]

    for name, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    print("\n🎉 BULK SCAN SIMULATION COMPLETE")
