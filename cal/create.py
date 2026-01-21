"""
Create calendar event functionality
"""

from datetime import datetime
from utils.graph_api import call_graph_api
from auth import ensure_authenticated
from server import mcp


@mcp.tool()
async def handle_create_event(
    subject: str = "",
    start_datetime: str = "",
    end_datetime: str = "",
    timezone: str = "America/Los_Angeles",
    location: str = "",
    body: str = "",
    is_all_day: bool = False,
    attendees: str = "",
) -> str:
    """
    Create a calendar event in Outlook

    Args:
        subject: Event title/subject (required)
        start_datetime: Start date and time in ISO format (YYYY-MM-DDTHH:MM:SS) (required)
        end_datetime: End date and time in ISO format (YYYY-MM-DDTHH:MM:SS) (required)
        timezone: Timezone for the event (default: America/Los_Angeles)
        location: Event location (optional)
        body: Event description/body content (optional)
        is_all_day: Whether this is an all-day event (default: False)
        attendees: Comma-separated email addresses of attendees (optional)

    Returns:
        Success message with event details or error message if creation failed
    """

    if not subject:
        return "Subject is required."

    if not start_datetime:
        return "Start datetime is required (format: YYYY-MM-DDTHH:MM:SS)."

    if not end_datetime:
        return "End datetime is required (format: YYYY-MM-DDTHH:MM:SS)."

    try:
        access_token = await ensure_authenticated()
        if not access_token:
            return "Authentication required. Please use the 'handle_authenticate' tool first."

        event_data = {
            "subject": subject,
            "start": {
                "dateTime": start_datetime,
                "timeZone": timezone,
            },
            "end": {
                "dateTime": end_datetime,
                "timeZone": timezone,
            },
            "isAllDay": is_all_day,
        }

        if location:
            event_data["location"] = {"displayName": location}

        if body:
            event_data["body"] = {
                "contentType": "text",
                "content": body,
            }

        if attendees:
            event_data["attendees"] = [
                {
                    "emailAddress": {"address": email.strip()},
                    "type": "required",
                }
                for email in attendees.split(",")
                if email.strip()
            ]

        result = await call_graph_api(access_token, "POST", "me/events", event_data)

        event_id = result.get("id", "unknown")
        web_link = result.get("webLink", "")

        return (
            f"Event created successfully!\n\n"
            f"Subject: {subject}\n"
            f"Start: {start_datetime} ({timezone})\n"
            f"End: {end_datetime} ({timezone})\n"
            f"{f'Location: {location}' if location else ''}\n"
            f"{f'Link: {web_link}' if web_link else ''}"
        )

    except Exception as e:
        if str(e) == "Authentication required" or str(e) == "UNAUTHORIZED":
            return "Authentication required. Please use the 'handle_authenticate' tool first."

        return f"Error creating event: {str(e)}"
