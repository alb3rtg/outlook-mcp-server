"""
List emails functionality
"""

from typing import Dict, Optional
from config import MAX_RESULT_COUNT, EMAIL_SELECT_FIELDS
from utils.graph_api import call_graph_api
from auth import ensure_authenticated
from .folder_utils import resolve_folder_path
from server import mcp


@mcp.tool()
async def handle_list_emails(
    folder: str = "inbox",
    count: int = 10,
) -> str:
    """
    List emails from a specified Outlook folder

    Args:
        folder: The email folder to list emails from (default: "inbox")
        count: Maximum number of emails to retrieve (default: 10)

    Returns:
        Formatted string containing email list with sender, subject, date, and read status
    """

    count = min(count, MAX_RESULT_COUNT)

    try:
        # Get access token
        access_token = await ensure_authenticated()
        if not access_token:
            return "Authentication required. Please use the 'authenticate' tool first."

        # Resolve folder path
        endpoint = await resolve_folder_path(access_token, folder)

        # Add query parameters
        query_params = {
            "$top": count,
            "$orderby": "receivedDateTime desc",
            "$select": EMAIL_SELECT_FIELDS,
        }

        # Make API call
        response = await call_graph_api(
            access_token, "GET", endpoint, None, query_params
        )

        if not response.get("value") or len(response["value"]) == 0:
            return f"No emails found in {folder}."

        # Format results
        email_list = []
        for index, email in enumerate(response["value"], 1):
            sender = email.get("from", {}).get(
                "emailAddress", {"name": "Unknown", "address": "unknown"}
            )
            date = email["receivedDateTime"]
            read_status = "" if email.get("isRead", True) else "[UNREAD] "

            email_list.append(
                f"{index}. {read_status}{date} - From: {sender['name']} ({sender['address']})\n"
                f"Subject: {email['subject']}\n"
                f"ID: {email['id']}\n"
            )

        return f"Found {len(response['value'])} emails in {folder}:\n\n{''.join(email_list)}"

    except Exception as e:
        if str(e) == "Authentication required":
            return "Authentication required. Please use the 'authenticate' tool first."

        return f"Error listing emails: {str(e)}"
