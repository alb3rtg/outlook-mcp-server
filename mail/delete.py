"""
Delete email functionality
"""

from utils.graph_api import call_graph_api
from auth import ensure_authenticated
from logger import logger
from server import mcp


@mcp.tool()
async def handle_delete_email(id: str) -> str:
    """
    Delete a specific email by its ID

    Args:
        id: The unique identifier of the email to delete

    Returns:
        Confirmation message on success, error message on failure
    """
    email_id = id

    if not email_id:
        return "Email ID is required."

    try:
        access_token = await ensure_authenticated()
        if not access_token:
            return "Authentication required. Please use the 'authenticate' tool first."

        try:
            await call_graph_api(access_token, "DELETE", f"me/messages/{email_id}")
            return f"Email {email_id} deleted successfully."

        except Exception as e:
            logger.error(f"Error deleting email: {str(e)}")
            if "doesn't belong to the targeted mailbox" in str(e):
                return "The email ID seems invalid or doesn't belong to your mailbox."
            return f"Failed to delete email: {str(e)}"

    except Exception as e:
        if str(e) == "Authentication required":
            return "Authentication required. Please use the 'authenticate' tool first."
        return f"Error deleting email: {str(e)}"
