"""
Email folder utilities
"""

import logging
from typing import Dict, List, Optional
from utils.graph_api import call_graph_api

logger = logging.getLogger(__name__)

# Cache of folder information to reduce API calls
# Format: { userId: { folderName: { id, path } } }
folder_cache: Dict[str, Dict[str, Dict[str, str]]] = {}


async def resolve_folder_path(access_token: str, folder_name: str) -> str:
    """
    Resolve a folder name to its endpoint path

    Args:
        access_token: Access token
        folder_name: Folder name to resolve

    Returns:
        Resolved endpoint path
    """
    # Default to inbox if no folder specified
    if not folder_name:
        return "me/messages"

    # Handle well-known folder names
    well_known_folders = {
        "inbox": "me/messages",
        "drafts": "me/mailFolders/drafts/messages",
        "sent": "me/mailFolders/sentItems/messages",
        "deleted": "me/mailFolders/deletedItems/messages",
        "junk": "me/mailFolders/junkemail/messages",
        "archive": "me/mailFolders/archive/messages",
    }

    # Check if it's a well-known folder (case-insensitive)
    lower_folder_name = folder_name.lower()
    if lower_folder_name in well_known_folders:
        logger.info(f"Using well-known folder path for '{folder_name}'")
        return well_known_folders[lower_folder_name]

    try:
        # Try to find the folder by name
        folder_id = await get_folder_id_by_name(access_token, folder_name)
        if folder_id:
            path = f"me/mailFolders/{folder_id}/messages"
            logger.info(f"Resolved folder '{folder_name}' to path: {path}")
            return path

        # If not found, fall back to inbox
        logger.info(f"Couldn't find folder '{folder_name}', falling back to inbox")
        return "me/messages"
    except Exception as e:
        logger.error(f"Error resolving folder '{folder_name}': {str(e)}")
        return "me/messages"


async def get_folder_id_by_name(access_token: str, folder_name: str) -> Optional[str]:
    """
    Get the ID of a mail folder by its name

    Args:
        access_token: Access token
        folder_name: Name of the folder to find

    Returns:
        Folder ID or None if not found
    """
    try:
        # First try with exact match filter
        logger.info(f"Looking for folder with name '{folder_name}'")
        response = await call_graph_api(
            access_token,
            "GET",
            "me/mailFolders",
            None,
            {"$filter": f"displayName eq '{folder_name}'"},
        )

        if response.get("value") and len(response["value"]) > 0:
            logger.info(
                f"Found folder '{folder_name}' with ID: {response['value'][0]['id']}"
            )
            return response["value"][0]["id"]

        # If exact match fails, try to get all folders and do a case-insensitive comparison
        logger.info(
            f"No exact match found for '{folder_name}', trying case-insensitive search"
        )
        all_folders_response = await call_graph_api(
            access_token, "GET", "me/mailFolders", None, {"$top": 100}
        )

        if all_folders_response.get("value"):
            lower_folder_name = folder_name.lower()
            matching_folder = next(
                (
                    folder
                    for folder in all_folders_response["value"]
                    if folder["displayName"].lower() == lower_folder_name
                ),
                None,
            )

            if matching_folder:
                logger.info(
                    f"Found case-insensitive match for '{folder_name}' with ID: {matching_folder['id']}"
                )
                return matching_folder["id"]

        logger.info(f"No folder found matching '{folder_name}'")
        return None
    except Exception as e:
        logger.error(f"Error finding folder '{folder_name}': {str(e)}")
        return None


async def get_all_folders(access_token: str) -> List[Dict]:
    """
    Get all mail folders

    Args:
        access_token: Access token

    Returns:
        Array of folder objects
    """
    try:
        # Get top-level folders
        response = await call_graph_api(
            access_token,
            "GET",
            "me/mailFolders",
            None,
            {
                "$top": 100,
                "$select": "id,displayName,parentFolderId,childFolderCount,totalItemCount,unreadItemCount",
            },
        )

        if not response.get("value"):
            return []

        # Get child folders for folders with children
        folders_with_children = [
            f for f in response["value"] if f["childFolderCount"] > 0
        ]

        child_folder_promises = []
        for folder in folders_with_children:
            try:
                child_response = await call_graph_api(
                    access_token,
                    "GET",
                    f"me/mailFolders/{folder['id']}/childFolders",
                    None,
                    {
                        "$select": "id,displayName,parentFolderId,childFolderCount,totalItemCount,unreadItemCount"
                    },
                )
                child_folder_promises.append(child_response.get("value", []))
            except Exception as e:
                logger.error(
                    f"Error getting child folders for '{folder['displayName']}': {str(e)}"
                )
                child_folder_promises.append([])

        # Combine top-level folders and all child folders
        return response["value"] + [
            folder for folders in child_folder_promises for folder in folders
        ]
    except Exception as e:
        logger.error(f"Error getting all folders: {str(e)}")
        return []


__all__ = ["resolve_folder_path", "get_folder_id_by_name", "get_all_folders"]
