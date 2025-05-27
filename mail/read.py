"""
Read email functionality
"""

import re
from typing import Dict, Optional
from config import EMAIL_DETAIL_FIELDS
from utils.graph_api import call_graph_api
from auth import ensure_authenticated
from logger import logger
from server import mcp


@mcp.tool()
async def handle_read_email(id: str) -> str:
    """
    Read a specific email by its ID and return detailed content

    Args:
        id: The unique identifier of the email to read

    Returns:
        Formatted string containing complete email details including sender, recipients,
        subject, date, importance, attachments status, and full body content
    """
    email_id = id

    if not email_id:
        return "Email ID is required."

    try:
        # Get access token
        access_token = await ensure_authenticated()
        if not access_token:
            return "Authentication required. Please use the 'authenticate' tool first."

        # Make API call to get email details
        endpoint = f"me/messages/{email_id}"
        query_params = {"$select": EMAIL_DETAIL_FIELDS}

        try:
            email = await call_graph_api(
                access_token, "GET", endpoint, None, query_params
            )

            if not email:
                return f"Email with ID {email_id} not found."

            # Format sender, recipients, etc.
            sender = email.get("from", {}).get("emailAddress", {})
            sender_str = (
                f"{sender.get('name', 'Unknown')} ({sender.get('address', 'unknown')})"
            )

            to = (
                ", ".join(
                    f"{r['emailAddress']['name']} ({r['emailAddress']['address']})"
                    for r in email.get("toRecipients", [])
                )
                or "None"
            )

            cc = (
                ", ".join(
                    f"{r['emailAddress']['name']} ({r['emailAddress']['address']})"
                    for r in email.get("ccRecipients", [])
                )
                or "None"
            )

            bcc = (
                ", ".join(
                    f"{r['emailAddress']['name']} ({r['emailAddress']['address']})"
                    for r in email.get("bccRecipients", [])
                )
                or "None"
            )

            date = email["receivedDateTime"]

            # Extract body content
            body = ""
            if email.get("body"):
                if email["body"].get("contentType") == "html":
                    # Simple HTML-to-text conversion for HTML bodies
                    body = re.sub(r"<[^>]*>", "", email["body"]["content"])
                else:
                    body = email["body"]["content"]
            else:
                body = email.get("bodyPreview", "No content")

            # Format the email
            formatted_email = (
                f"From: {sender_str}\n"
                f"To: {to}\n"
                + (f"CC: {cc}\n" if cc != "None" else "")
                + (f"BCC: {bcc}\n" if bcc != "None" else "")
                + f"Subject: {email['subject']}\n"
                f"Date: {date}\n"
                f"Importance: {email.get('importance', 'normal')}\n"
                f"Has Attachments: {'Yes' if email.get('hasAttachments') else 'No'}\n\n"
                f"{body}"
            )

            return formatted_email

        except Exception as e:
            logger.error(f"Error reading email: {str(e)}")

            # Improved error handling with more specific messages
            if "doesn't belong to the targeted mailbox" in str(e):
                return "The email ID seems invalid or doesn't belong to your mailbox. Please try with a different email ID."
            else:
                return f"Failed to read email: {str(e)}"

    except Exception as e:
        if str(e) == "Authentication required":
            return "Authentication required. Please use the 'authenticate' tool first."

        return f"Error accessing email: {str(e)}"
