"""
Microsoft Graph API helper functions
"""

import json
import logging
import urllib.parse
import aiohttp
from typing import Dict, Any, Optional
from config import GRAPH_API_ENDPOINT

logger = logging.getLogger(__name__)


async def call_graph_api(
    access_token: str,
    method: str,
    path: str,
    data: Optional[Dict] = None,
    query_params: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Makes a request to the Microsoft Graph API

    Args:
        access_token: The access token for authentication
        method: HTTP method (GET, POST, etc.)
        path: API endpoint path
        data: Data to send for POST/PUT requests
        query_params: Query parameters

    Returns:
        The API response

    Raises:
        Exception: If the API call fails
    """
    try:
        logger.debug(f"Making real API call: {method} {path}")

        # Encode path segments properly
        encoded_path = "/".join(
            urllib.parse.quote(segment) for segment in path.split("/")
        )

        # Build query string from parameters with special handling for OData filters
        query_string = ""
        if query_params:
            # Handle $filter parameter specially to ensure proper URI encoding
            filter_value = query_params.pop("$filter", None)

            # Build query string with proper encoding for regular params
            params = urllib.parse.urlencode(query_params)

            # Add filter parameter separately with proper encoding
            if filter_value:
                if params:
                    params += f"&$filter={urllib.parse.quote(filter_value)}"
                else:
                    params = f"$filter={urllib.parse.quote(filter_value)}"

            if params:
                query_string = f"?{params}"

            logger.debug(f"Query string: {query_string}")

        url = f"{GRAPH_API_ENDPOINT}{encoded_path}{query_string}"
        logger.debug(f"Full URL: {url}")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                url,
                headers=headers,
                json=data if data and method in ("POST", "PATCH", "PUT") else None,
            ) as response:
                response_data = await response.text()

                if 200 <= response.status < 300:
                    try:
                        return json.loads(response_data)
                    except json.JSONDecodeError as e:
                        raise Exception(f"Error parsing API response: {str(e)}")
                elif response.status == 401:
                    # Token expired or invalid
                    raise Exception("UNAUTHORIZED")
                else:
                    raise Exception(
                        f"API call failed with status {response.status}: {response_data}"
                    )

    except Exception as e:
        logger.error(f"Error calling Graph API: {str(e)}")
        raise


__all__ = ["call_graph_api"]
