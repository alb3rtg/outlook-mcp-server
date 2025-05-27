"""
Authentication-related tools for the Outlook MCP server
"""

__all__ = ["handle_about", "handle_authenticate", "handle_check_auth_status"]

import time
import logging
from config import settings
from .token_manager import load_token_cache
from server import mcp

logger = logging.getLogger(__name__)


@mcp.tool()
async def handle_about() -> str:
    """
    About tool handler - provides information about the Outlook MCP server
    
    Returns:
        String containing server information including name, version, capabilities,
        and available features for managing Outlook emails and calendar events
    """
    return (
        f"📧 MODULAR Outlook Assistant MCP Server v{settings.SERVER_VERSION} 📧\n\n"
        f"Provides access to Microsoft Outlook email, calendar, and contacts through Microsoft Graph API.\n"
        f"Implemented with a modular architecture for improved maintainability."
    )


@mcp.tool()
async def handle_authenticate(force: bool = False) -> str:
    """
    Authentication tool handler - manages Microsoft Graph API authentication for Outlook access
    
    Args:
        force: Whether to force re-authentication even if valid tokens exist (default: False)
        
    Returns:
        Authentication status message indicating success, failure, or instructions for
        completing the OAuth flow to access Outlook services
    """
    auth_url = f"{settings.MS_AUTH_SERVER_URL}/auth"

    return (
        f"Authentication required. Please visit the following URL to authenticate with Microsoft: {auth_url}\n\n"
        f"After authentication, you will be redirected back to this application."
    )


@mcp.tool()
async def handle_check_auth_status() -> str:
    """
    Check authentication status tool handler - verifies current Microsoft Graph API authentication state
    
    Returns:
        String containing current authentication status, token validity, expiration details,
        and whether the user is properly authenticated to access Outlook services
    """
    logger.info("Starting authentication status check")

    tokens = load_token_cache()

    logger.info(f"Tokens loaded: {'YES' if tokens else 'NO'}")

    if not tokens or not tokens.get("access_token"):
        logger.info("No valid access token found")
        return "Not authenticated"

    logger.info("Access token present")
    logger.info(f"Token expires at: {tokens.get('expires_at')}")
    logger.info(f"Current time: {int(time.time() * 1000)}")

    return "Authenticated and ready"
