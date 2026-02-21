# Step-by-Step Setup Guide

## Prerequisites

- Microsoft 365 account (work/school) OR Outlook.com account
- Access to Power Automate (included with Microsoft 365, or free tier available)

### Connectors Required
| Connector | Flow | Purpose |
|-----------|------|---------|
| Office 365 Outlook | Both | Email operations (read, move, delete, send) |
| Office 365 Users | Weekly Purge | Get your email for sending reports |
| HTTP | Main Flow | Call unsubscribe URLs (may require Premium) |

---

## Part 1: Create the Required Folder

Before setting up the flows, create the destination folder in Outlook:

1. Open [Outlook Web](https://outlook.office.com) in Chrome
2. Right-click on **Folders** in the left sidebar
3. Select **Create new folder**
4. Name it: `Promotional-ToDelete`
5. Press Enter

---

## Part 2: Import the Main Flow

### Option A: Import JSON (Recommended)

1. Go to [flow.microsoft.com](https://flow.microsoft.com)
2. Sign in with your Microsoft account
3. Click **My flows** in the left sidebar
4. Click **Import** → **Import Package (Legacy)**
5. Click **Upload** and select `sales-email-manager-flow.json`
6. Under "Related resources", click **Select during import** for the Office 365 connection
7. Either select an existing connection or create a new one
8. Click **Import**
9. Open the imported flow and click **Turn on**

### Option B: Build Manually

If import doesn't work, follow these steps:

#### Step 1: Create New Flow

1. Go to [flow.microsoft.com](https://flow.microsoft.com)
2. Click **+ Create** → **Automated cloud flow**
3. Name it: `Smart Sales Email Manager`
4. Search for trigger: "When a new email arrives (V3)"
5. Select **When a new email arrives (V3) - Office 365 Outlook**
6. Click **Create**

#### Step 2: Configure Trigger

1. Set **Folder**: Inbox
2. Set **Include Attachments**: No
3. Expand **Advanced options**:
   - Only with Attachments: No
   - Importance: Any

#### Step 3: Add Variables

Click **+ New step** and add these Initialize Variable actions:

| Variable Name | Type | Initial Value |
|---------------|------|---------------|
| unsubscribeLink | String | (empty) |
| senderDomain | String | (empty) |
| isPromotional | Boolean | false |
| isSafeToUnsubscribe | Boolean | false |

#### Step 4: Extract Sender Domain

1. Click **+ New step** → **Compose** (under Data Operations)
2. Rename to: `Extract Sender Domain`
3. In Inputs, use expression:
```
if(contains(triggerBody()?['from'], '@'), last(split(triggerBody()?['from'], '@')), '')
```

4. Add **Set Variable**:
   - Name: senderDomain
   - Value: Output of previous compose (clean it with replace for > and spaces)

#### Step 5: Check If Promotional

1. Add **Compose** action, rename to: `Check If Promotional`
2. Use this expression:
```
or(
  contains(toLower(triggerBody()?['body']), 'unsubscribe'),
  contains(toLower(triggerBody()?['subject']), 'offer'),
  contains(toLower(triggerBody()?['subject']), 'discount'),
  contains(toLower(triggerBody()?['subject']), 'sale'),
  contains(toLower(triggerBody()?['subject']), 'deal'),
  contains(toLower(triggerBody()?['subject']), 'limited time'),
  contains(toLower(triggerBody()?['subject']), 'act now'),
  contains(toLower(triggerBody()?['subject']), 'exclusive'),
  contains(toLower(triggerBody()?['subject']), 'free'),
  contains(toLower(triggerBody()?['body']), 'promotional'),
  contains(toLower(triggerBody()?['body']), 'marketing email')
)
```

3. Add **Set Variable** for isPromotional with output

#### Step 6: Add Main Condition

1. Add **Condition** action
2. Set: `isPromotional` is equal to `true`

#### Step 7: Inside "If Yes" Branch

**A. Extract Unsubscribe Link:**
1. Add **Compose**: `Extract Unsubscribe Link`
2. Expression (simplified):
```
if(contains(toLower(triggerBody()?['body']), 'unsubscribe'),
   first(split(last(split(toLower(triggerBody()?['body']), 'href="')), '"')),
   '')
```

**B. Check Link Safety:**
1. Add **Compose**: `Check Link Safety`
2. Expression:
```
and(
  startsWith(variables('unsubscribeLink'), 'https://'),
  not(contains(variables('unsubscribeLink'), 'bit.ly')),
  not(contains(variables('unsubscribeLink'), 'tinyurl')),
  not(contains(variables('unsubscribeLink'), 't.co/')),
  not(contains(variables('unsubscribeLink'), 'goo.gl')),
  not(empty(variables('unsubscribeLink')))
)
```

**C. Check Domain Matches:**
1. Add **Compose**: `Check Domain Match`
2. Expression (checks sender domain OR known email providers):
```
or(
  contains(variables('unsubscribeLink'), variables('senderDomain')),
  contains(variables('unsubscribeLink'), 'mailchimp.com'),
  contains(variables('unsubscribeLink'), 'sendgrid.net'),
  contains(variables('unsubscribeLink'), 'constantcontact.com'),
  contains(variables('unsubscribeLink'), 'hubspot.com'),
  contains(variables('unsubscribeLink'), 'list-manage.com'),
  contains(variables('unsubscribeLink'), 'campaign-archive.com')
)
```

**D. Set Safety Flag:**
1. Add **Set Variable** for `isSafeToUnsubscribe`
2. Value: `and(outputs('Check_Link_Safety'), outputs('Check_Domain_Match'))`

**E. Add Nested Condition for Unsubscribe:**
1. Add **Condition**: `isSafeToUnsubscribe` equals `true`
2. In "If Yes":
   - Add **HTTP** action:
     - Method: GET
     - URI: `@{variables('unsubscribeLink')}`
     - Headers: `User-Agent: Mozilla/5.0`

**F. Move Email (after nested condition):**
1. Add **Move email (V2)**:
   - Message Id: Use dynamic content from trigger
   - Destination folder: `Promotional-ToDelete`

**G. Mark as Read:**
1. Add **Mark as read or unread (V3)**:
   - Message Id: Use dynamic content from trigger
   - Mark as: Read

#### Step 8: Save and Test

1. Click **Save**
2. Click **Test** → **Manually** → **Test**
3. Send yourself a test promotional email
4. Check the flow run history

---

## Part 3: Import the Weekly Purge Flow

Repeat the import process with `weekly-purge-flow.json`.

**This flow includes:**
- Runs every Sunday at 3:00 AM (Pacific Time)
- Deletes emails older than 7 days from `Promotional-ToDelete`
- Sends you an HTML email report with:
  - Summary: emails deleted, emails kept, total processed
  - Table listing every deleted email (from, subject, date)

**Additional Setup for Weekly Purge:**
1. When importing, configure **two** connections:
   - Office 365 Outlook (for email operations)
   - Office 365 Users (for getting your email address)
2. If Office 365 Users connection isn't available, you can edit the flow after import to hardcode your email in the "Send Report Email" action

**Manual Build (if import fails):**
1. Create **Scheduled cloud flow**
2. Set recurrence: Weekly, Sunday at 3:00 AM
3. Add **Get my profile (V2)** from Office 365 Users
4. Add **Get emails (V2)** from `Promotional-ToDelete` folder
5. Initialize variables: `deletedCount`, `deletedEmailsList`, `skippedCount`
6. Add **For each** loop over emails
7. Inside loop: **Condition** to check if email is older than 7 days
8. If yes: Append to list, **Delete email (V2)**, increment counter
9. After loop: **Send an email (V2)** with HTML report to your email

---

## Part 4: Customize Keywords (Optional)

Edit the promotional detection keywords in the main flow:

### Add More Keywords
In the `Check If Promotional` compose action, add more terms:
```
contains(toLower(triggerBody()?['subject']), 'your-keyword'),
```

### Suggested Keywords to Add
- `newsletter`
- `weekly digest`
- `monthly update`
- `special offer`
- `dont miss`
- `expires`
- `last chance`
- `reminder`
- `webinar`
- `invitation`

### Add More Trusted Email Providers
In `Check Domain Match`, add:
```
contains(variables('unsubscribeLink'), 'provider-domain.com'),
```

---

## Part 5: Monitoring and Logs

### View Run History
1. Go to **My flows**
2. Click on your flow name
3. Click **28 day run history** to see executions
4. Click any run to see details and debug

### Check for Errors
- Failed runs show in red
- Click to see which step failed and why
- Common issues:
  - Connection expired: Re-authenticate
  - Folder not found: Create the folder
  - HTTP timeout: Link was slow/unavailable

---

## Troubleshooting

### Flow Not Triggering
- Ensure flow is turned **On**
- Check the connection is authorized
- Verify folder path is "Inbox" (case-sensitive)

### Emails Not Being Detected
- Check if email body actually contains keywords
- Test with exact keywords from the detection list
- Some emails use images instead of text

### Unsubscribe Not Working
- Link might require POST instead of GET
- Some links need form submission
- Link might be expired or one-time use

### Folder Errors
- Create `Promotional-ToDelete` folder manually
- Check for typos in folder name
- Folder names are case-sensitive

---

## Security Notes

1. **The flow never unsubscribes from suspicious links** - only HTTPS links from verified domains
2. **Review the "Promotional-ToDelete" folder periodically** - ensure no legitimate emails are caught
3. **Add important senders to your Safe Senders list** in Outlook to exclude them
4. **Check run history** if you're missing expected emails

---

## Estimated Costs

- **Microsoft 365 subscribers**: Included in subscription
- **Free tier**: 750 runs/month (usually sufficient for personal use)
- **Premium features** (like HTTP actions): May require paid plan

Check your plan at [flow.microsoft.com/pricing](https://flow.microsoft.com/pricing)
