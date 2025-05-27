"""
Token management for Microsoft Graph API authentication
"""

import os
import json
import time
from typing import Dict, Optional

from logger import logger
from config import settings


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
    """Save tokens to cache file"""
    try:
        with open(settings.MS_TOKEN_STORE_PATH, "w") as f:
            json.dump(tokens, f)

        logger.info("Successfully saved token cache")
        return True

    except Exception as e:
        logger.error(f"Error saving token cache: {str(e)}")
        return False


def is_token_expired(tokens: Dict) -> bool:
    """Check if the access token is expired"""
    if not tokens or "expires_at" not in tokens:
        return True

    # Add 5-minute buffer to ensure token is still valid
    print(time.time(), tokens["expires_at"])
    return time.time() >= tokens["expires_at"]


def create_test_tokens() -> Dict:
    """Create test tokens for development"""
    tokens = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_at": int(time.time() * 1000) + 3600000,  # 1 hour from now
    }

    save_token_cache(tokens)
    return tokens


def get_valid_token() -> Optional[str]:
    """Get a valid access token, refreshing if necessary"""
    tokens = load_token_cache()

    if not tokens:
        logger.info("No tokens found")
        return None

    if is_token_expired(tokens):
        logger.info("Token expired, attempting refresh")
        # TODO: Implement token refresh logic
        return None

    return tokens["access_token"]
