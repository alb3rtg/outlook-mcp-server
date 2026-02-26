# Task: Power Automate Email Manager

Reference: Read META-TASK-WORKFLOW.md

---

## Status: ACTIVE

## Platform: Mac

## Target Account

- **Email**: albert.greenberg@hotmail.com
- **Type**: Outlook.com (Personal Microsoft Account)
- **Power Automate**: [flow.microsoft.com](https://flow.microsoft.com) (sign in with Hotmail)

## Objective

Create a Microsoft Power Automate solution that:
1. Automatically identifies corporate/promotional sales emails
2. Safely unsubscribes from legitimate senders (HTTPS, domain-verified)
3. Moves promotional emails to a staging folder
4. Bulk deletes old promotional emails weekly
5. Sends a weekly report of deleted emails

## Files

| File | Description |
|------|-------------|
| `power-automate-email-manager/sales-email-manager-flow.json` | Main flow - processes NEW incoming emails |
| `power-automate-email-manager/bulk-scan-flow.json` | One-time scan - processes EXISTING inbox (run manually) |
| `power-automate-email-manager/weekly-purge-flow.json` | Weekly cleanup - deletes ALL emails in folder, sends report |
| `power-automate-email-manager/README.md` | Overview and quick start |
| `power-automate-email-manager/SETUP-GUIDE.md` | Detailed manual setup instructions |
| `power-automate-email-manager/QUICK-IMPORT-STEPS.md` | 5-minute import guide |
| `power-automate-email-manager/sandbox/test_sandbox.py` | Unit tests for all components (37 tests) |
| `power-automate-email-manager/sandbox/e2e_simulation.py` | End-to-end flow simulation |
| `power-automate-email-manager/sandbox/bulk_scan_simulation.py` | Bulk scan simulation (5000 emails) |

## How It Works

### Flow 0: Bulk Scan (manual, for existing emails)
```
MANUALLY TRIGGERED (click "Run" button)
    │
    ▼
Search Inbox for emails containing:
    "unsubscribe" OR subject has offer/discount/sale/deal/etc.
    │
    ▼
For each email found (up to 250 per run):
    - Move to "Promotional-ToDelete" folder
    │
    ▼
Send report: "X promotional emails found and moved"

REPEAT until no more promotional emails found
```

### Flow 1: Sales Email Manager (triggers on new email)
```
New Email Arrives
    │
    ▼
Check Keywords (subject: offer, discount, sale, deal, etc.)
Check Body (unsubscribe, promotional, marketing email)
    │
    ├─ Not Promotional → KEEP (no action)
    │
    └─ Promotional → Extract unsubscribe link
                         │
                         ▼
                    Safety Checks:
                    ✓ HTTPS only
                    ✓ No URL shorteners (bit.ly, t.co, etc.)
                    ✓ Domain matches sender OR trusted provider
                         │
                         ├─ SAFE → HTTP GET unsubscribe link
                         │
                         └─ UNSAFE → Skip unsubscribe
                         │
                         ▼
                    Move to "Promotional-ToDelete" folder
                    Mark as read
```

### Flow 2: Weekly Purge (Sunday 3am)
```
Get ALL emails from "Promotional-ToDelete" folder
    │
    ▼
For EACH email (no age limit):
    - Record sender, subject, date
    - Delete email
    │
    ▼
Send HTML report email with:
    - Summary (total deleted count)
    - Table of all deleted emails
```

## Safety Features

- **HTTPS only** - Never clicks HTTP links
- **No URL shorteners** - Blocks bit.ly, tinyurl, t.co, goo.gl, etc.
- **Domain verification** - Unsubscribe link must match sender domain
- **Trusted providers whitelist** - Mailchimp, SendGrid, HubSpot, etc.
- **Review period** - Emails sit in staging folder until next weekly purge
- **Weekly report** - Full audit trail of what was deleted

## Acceptance Criteria

- [x] JSON flows are valid and importable
- [x] Logic correctly identifies promotional emails (tested with 8 cases)
- [x] Safety checks block suspicious unsubscribe links
- [x] Safety checks allow legitimate unsubscribe links
- [x] Non-promotional emails are untouched
- [x] Weekly purge sends email report
- [ ] Manual test in Power Automate (requires import)

## Testing

### Unit Tests (37 tests - ALL PASSED)
```bash
cd ~/Projects/outlook-mcp-server/power-automate/sandbox
python3 test_sandbox.py
```

| Component | Tests | Status |
|-----------|-------|--------|
| Promotional Detection | 8 | ✅ PASS |
| Sender Domain Extraction | 5 | ✅ PASS |
| Unsubscribe Link Extraction | 4 | ✅ PASS |
| Safety Check | 11 | ✅ PASS |
| Main Flow Integration | 4 | ✅ PASS |
| Weekly Purge | 5 | ✅ PASS |

### End-to-End Simulation (ALL PASSED)
```bash
cd ~/Projects/outlook-mcp-server/power-automate/sandbox
python3 e2e_simulation.py
```

Simulated 18 emails through complete flow:
- ✅ 5 legitimate emails kept (meetings, orders, GitHub)
- ✅ 5 promotional emails unsubscribed + moved (BestBuy, TechCrunch, HubSpot, Medium, Mailchimp)
- ✅ 5 unsafe promotional emails moved only (bit.ly, domain mismatch, HTTP, no link)
- ✅ 13 emails deleted in weekly purge (ALL emails in folder, no age limit)
- ✅ Weekly report generated to albert.greenberg@hotmail.com

## Manual Deployment

1. Create folder `Promotional-ToDelete` in Outlook Web
2. Go to [flow.microsoft.com](https://flow.microsoft.com)
3. Import `sales-email-manager-flow.json`
4. Import `weekly-purge-flow.json` (requires Office 365 Users connector for report)
5. Turn on both flows
6. Test by sending promotional email to yourself

## Connectors Required

| Connector | Used By | Purpose |
|-----------|---------|---------|
| Office 365 Outlook | Both flows | Read/move/delete emails, send report |
| Office 365 Users | Weekly Purge | Get user email for report recipient |
| HTTP | Main flow | Call unsubscribe URLs |

## Known Limitations

- Can only process ~250 emails per purge run (API limit)
- Some emails use images instead of text (won't detect keywords)
- Unsubscribe links requiring POST/form submission won't work
- HTTP connector may require Power Automate Premium

## Artifacts

Location: `~/Projects/outlook-mcp-server/power-automate/`

## Sync

```bash
cd ~/Projects/dotfiles && git add -A && git commit -m "Update power-automate-email-manager" && git push
```
