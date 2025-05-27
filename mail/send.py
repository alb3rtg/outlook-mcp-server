"""
Send email functionality
"""

from utils.graph_api import call_graph_api
from auth import ensure_authenticated
from server import mcp


@mcp.tool()
async def handle_send_email(
    to: str = "",
    cc: str = "",
    subject: str = "",
    body: str = "",
    importance: str = "normal",
    save_to_sent_items: bool = True,
) -> str:
    """
    Send an email through Outlook with specified recipients and content

    Args:
        to: Primary recipient email addresses (comma-separated for multiple recipients)
        cc: Carbon copy recipient email addresses (comma-separated for multiple recipients)
        subject: Email subject line
        body: Email body content (supports HTML formatting)
        importance: Email importance level ("low", "normal", or "high") (default: "normal")
        save_to_sent_items: Whether to save the email to Sent Items folder (default: True)

    Returns:
        Success message with sent email details or error message if sending failed
    """

    # Validate required parameters
    if not to:
        return "Recipient (to) is required."

    if not subject:
        return "Subject is required."

    if not body:
        return "Body content is required."

    try:
        # Get access token
        access_token = await ensure_authenticated()
        if not access_token:
            return "Authentication required. Please use the 'authenticate' tool first."

        # Format recipients
        to_recipients = [
            {"emailAddress": {"address": email.strip()}} for email in to.split(",")
        ]

        cc_recipients = [
            {"emailAddress": {"address": email.strip()}}
            for email in (cc or "").split(",")
            if email.strip()
        ]

        bcc_recipients = [
            {"emailAddress": {"address": email.strip()}}
            for email in (bcc or "").split(",")
            if email.strip()
        ]

        # Prepare email object
        email_object = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "html" if "<html" in body else "text",
                    "content": body,
                },
                "toRecipients": to_recipients,
                "importance": importance,
            },
            "saveToSentItems": save_to_sent_items,
        }

        # Add optional recipients
        if cc_recipients:
            email_object["message"]["ccRecipients"] = cc_recipients
        if bcc_recipients:
            email_object["message"]["bccRecipients"] = bcc_recipients

        # Make API call to send email
        await call_graph_api(access_token, "POST", "me/sendMail", email_object)

        return (
            f"Email sent successfully!\n\n"
            f"Subject: {subject}\n"
            f"Recipients: {len(to_recipients)}"
            f"{f' + {len(cc_recipients)} CC' if cc_recipients else ''}"
            f"{f' + {len(bcc_recipients)} BCC' if bcc_recipients else ''}\n"
            f"Message Length: {len(body)} characters"
        )
    except Exception as e:
        if str(e) == "Authentication required":
            return "Authentication required. Please use the 'authenticate' tool first."

        return f"Error sending email: {str(e)}"
