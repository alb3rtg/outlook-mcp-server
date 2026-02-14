__all__ = [
    "settings",
    "SERVER_VERSION",
    "MS_CLIENT_ID",
    "MS_CLIENT_SECRET",
    "MS_AUTH_SERVER_URL",
    "MS_SCOPES",
    "MS_TOKEN_STORE_PATH",
]

from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVER_NAME: str = "outlook-assistant"
    SERVER_VERSION: str = "v1.0.0"

    MS_CLIENT_ID: str
    MS_CLIENT_SECRET: str
    MS_AUTH_SERVER_URL: str = "http://localhost:3333"
    MS_SCOPES: List[str] = [
        "offline_access",
        "User.Read",
        "Mail.Read",
        "Mail.Send",
        "Calendars.Read",
        "Calendars.ReadWrite",
    ]
    MS_TOKEN_STORE_PATH: str = str(Path.home() / ".outlook-mcp-tokens.json")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
MS_CLIENT_ID = settings.MS_CLIENT_ID
MS_CLIENT_SECRET = settings.MS_CLIENT_SECRET
MS_AUTH_SERVER_URL = settings.MS_AUTH_SERVER_URL
MS_SCOPES = settings.MS_SCOPES
MS_TOKEN_STORE_PATH = settings.MS_TOKEN_STORE_PATH

SERVER_NAME = settings.SERVER_NAME
SERVER_VERSION = settings.SERVER_VERSION

# Microsoft Graph API
GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0/"

# Calendar constants
CALENDAR_SELECT_FIELDS = (
    "id,subject,bodyPreview,start,end,location,organizer,attendees,isAllDay,isCancelled"
)

# Email constants
EMAIL_SELECT_FIELDS = "id,subject,from,toRecipients,ccRecipients,receivedDateTime,bodyPreview,hasAttachments,importance,isRead"
EMAIL_DETAIL_FIELDS = "id,subject,from,toRecipients,ccRecipients,bccRecipients,receivedDateTime,bodyPreview,body,hasAttachments,importance,isRead,internetMessageHeaders"

# Pagination
DEFAULT_PAGE_SIZE = 25
MAX_RESULT_COUNT = 50
