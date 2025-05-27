"""
Main authentication module for the Outlook MCP server
"""

import logging
from typing import Optional
from .token_manager import get_valid_token
from .tools import *
from .tools import __all__ as tools_all

logger = logging.getLogger(__name__)


async def ensure_authenticated() -> Optional[str]:
    """
    Ensure the user is authenticated and return a valid access token.
    Returns None if not authenticated.
    """
    token = get_valid_token()

    if not token:
        logger.info("No valid token found, authentication required")
        return None

    logger.info("Valid token found")
    return token


# Export the token manager and auth tools
__all__ = ["ensure_authenticated"] + tools_all
