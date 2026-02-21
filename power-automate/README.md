# Power Automate: Smart Sales Email Manager

Automatically identifies promotional/sales emails, safely unsubscribes from legitimate senders, and bulk deletes them.

## Quick Start

1. Go to [flow.microsoft.com](https://flow.microsoft.com)
2. Sign in with your Microsoft/Outlook account
3. Click **My flows** → **Import** → **Import Package (Legacy)**
4. Upload `sales-email-manager-flow.json`
5. Configure your connections and activate

## Files Included

- `sales-email-manager-flow.json` - Main flow (processes incoming emails)
- `weekly-purge-flow.json` - Cleanup flow (deletes old flagged emails)
- `SETUP-GUIDE.md` - Detailed manual setup instructions

## What It Does

1. **Detects** promotional emails using keyword matching
2. **Extracts** unsubscribe links from email body
3. **Validates** links are safe (HTTPS, matching domain, no URL shorteners)
4. **Unsubscribes** automatically if link passes safety checks
5. **Moves** email to "Promotional-ToDelete" folder
6. **Purges** old emails weekly

## Safety Features

- Only unsubscribes via HTTPS links
- Blocks shortened URLs (bit.ly, tinyurl, t.co, etc.)
- Verifies unsubscribe domain matches sender domain
- Whitelist of known email service providers
- Never clicks suspicious or mismatched links
