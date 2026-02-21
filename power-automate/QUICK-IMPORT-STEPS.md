# Quick Import Steps (5 minutes)

## Before You Start
Create this folder in Outlook Web: `Promotional-ToDelete`

---

## Import Flow 1: Email Manager

1. Go to **[flow.microsoft.com](https://flow.microsoft.com)**
2. Sign in
3. **My flows** → **Import** → **Import Package (Legacy)**
4. Upload: `sales-email-manager-flow.json`
5. Configure Office 365 connection
6. Click **Import**
7. Open flow → **Turn on**

---

## Import Flow 2: Weekly Purge

1. Same steps as above
2. Upload: `weekly-purge-flow.json`
3. Turn on

---

## Test It

Send yourself an email with subject: "Special Discount Offer!"
And body containing: "Click here to unsubscribe"

Check:
- Flow run history shows success
- Email moved to `Promotional-ToDelete` folder

---

## Done!

Your flows will now run automatically 24/7.
