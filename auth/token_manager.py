"""
Token management for Microsoft Graph API authentication
"""

import os
import json
import time
import stat
import requests
from typing import Dict, Optional

from logger import logger
from config import settings


# Token file permissions (owner read/write only)
TOKEN_FILE_MODE = stat.S_IRUSR | stat.S_IWUSR  # 0o600


def load_token_cache() -> Optional[Dict]:
    """Load tokens from cache file"""
    try:
        if not os.path.exists(settings.MS_TOKEN_STORE_PATH):
            logger.info("No token cache file found")
            return None

        with open(settings.MS_TOKEN_STORE_PATH) as f:
            tokens = json.load(f)

        logger.info("Successfully loaded token cache")
        return tokens

    except Exception as e:
        logger.error(f"Error loading token cache: {str(e)}")
        return None


def save_token_cache(tokens: Dict) -> bool:
    """Save tokens to cache file with restrictive permissions"""
    try:
        token_path = settings.MS_TOKEN_STORE_PATH

        # Write to file
        with open(token_path, "w") as f:
            json.dump(tokens, f)

        # Set restrictive permissions (owner read/write only)
        os.chmod(token_path, TOKEN_FILE_MODE)

        logger.info("Successfully saved token cache with secure permissions")
        return True

    except Exception as e:
        logger.error(f"Error saving token cache: {str(e)}")
        return False


def is_token_expired(tokens: Dict) -> bool:
    """Check if the access token is expired"""
    if not tokens or "expires_at" not in tokens:
        return True

    # Add 5-minute buffer to ensure token is still valid
    buffer_seconds = 300  # 5 minutes
    return time.time() >= (tokens["expires_at"] - buffer_seconds)


def create_test_tokens() -> Dict:
    """Create test tokens for development"""
    tokens = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_at": int(time.time()) + 3600,  # 1 hour from now (in seconds)
    }

    save_token_cache(tokens)
    return tokens


def refresh_access_token(refresh_token: str) -> Optional[Dict]:
    """
    Refresh the access token using the refresh token

    Args:
        refresh_token: The refresh token from the previous authentication

    Returns:
        New token data or None if refresh failed
    """
    try:
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        token_data = {
            "client_id": settings.MS_CLIENT_ID,
            "client_secret": settings.MS_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "scope": " ".join(settings.MS_SCOPES),
        }

        response = requests.post(token_url, data=token_data, timeout=30)
        result = response.json()

        if "error" in result:
            logger.error(f"Token refresh failed: {result.get('error_description', 'Unknown error')}")
            return None

        # Calculate expiration time
        result["expires_at"] = int(time.time()) + result.get("expires_in", 3600)

        # Save the new tokens
        if save_token_cache(result):
            logger.info("Token refreshed successfully")
            return result

        return None

    except requests.RequestException as e:
        logger.error(f"Network error during token refresh: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        return None


def get_valid_token() -> Optional[str]:
    """Get a valid access token, refreshing if necessary"""
    tokens = load_token_cache()

    if not tokens:
        logger.info("No tokens found")
        return None

    if is_token_expired(tokens):
        logger.info("Token expired, attempting refresh")

        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            logger.error("No refresh token available")
            return None

        new_tokens = refresh_access_token(refresh_token)
        if new_tokens:
            return new_tokens["access_token"]

        logger.error("Token refresh failed, re-authentication required")
        return None

    return tokens["access_token"]
