"""
Outlook Authentication Server

A standalone server that handles Microsoft Graph API authentication
through OAuth 2.0 using FastAPI.
"""

import json
import os
import stat
import time
import secrets
import html
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
import uvicorn
import urllib.parse

from config import settings
from logger import logger

# Token file permissions (owner read/write only)
TOKEN_FILE_MODE = stat.S_IRUSR | stat.S_IWUSR  # 0o600

# Store for CSRF state tokens (in production, use Redis or similar)
# Maps state token -> timestamp for cleanup
_state_tokens: Dict[str, float] = {}
STATE_TOKEN_EXPIRY = 600  # 10 minutes


def generate_state_token() -> str:
    """Generate a cryptographically secure state token for CSRF protection"""
    # Clean up expired tokens
    current_time = time.time()
    expired = [k for k, v in _state_tokens.items() if current_time - v > STATE_TOKEN_EXPIRY]
    for k in expired:
        del _state_tokens[k]

    # Generate new token
    token = secrets.token_urlsafe(32)
    _state_tokens[token] = current_time
    return token


def validate_state_token(token: str) -> bool:
    """Validate a state token and remove it (one-time use)"""
    if token not in _state_tokens:
        return False

    timestamp = _state_tokens.pop(token)
    if time.time() - timestamp > STATE_TOKEN_EXPIRY:
        return False

    return True


def escape_html(text: str) -> str:
    """Escape HTML special characters to prevent XSS"""
    return html.escape(str(text)) if text else ""


# Create FastAPI app
app = FastAPI(
    title="Outlook Authentication Server",
    description="A server that handles Microsoft Graph API authentication through OAuth 2.0",
    version="1.0.0",
)

# HTML templates
TEMPLATES = {
    "error": """
        <html>
            <head>
                <title>{title}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }}
                    h1 {{ color: #d9534f; }}
                    .error-box {{ background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 4px; }}
                    code {{ background: #f4f4f4; padding: 2px 4px; border-radius: 4px; }}
                </style>
            </head>
            <body>
                <h1>{title}</h1>
                <div class="error-box">
                    {content}
                </div>
                <p>Please close this window and try again.</p>
            </body>
        </html>
    """,
    "success": """
        <html>
            <head>
                <title>Authentication Successful</title>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }}
                    h1 {{ color: #5cb85c; }}
                    .success-box {{ background-color: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 4px; }}
                </style>
            </head>
            <body>
                <h1>Authentication Successful!</h1>
                <div class="success-box">
                    <p>You have successfully authenticated with Microsoft Graph API.</p>
                    <p>The access token has been saved securely.</p>
                </div>
                <p>You can now close this window and return to Claude.</p>
            </body>
        </html>
    """,
    "root": """
        <html>
            <head>
                <title>Outlook Authentication Server</title>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                    h1 {{ color: #0078d4; }}
                    .info-box {{ background-color: #e7f6fd; border: 1px solid #b3e0ff; padding: 15px; border-radius: 4px; }}
                    code {{ background: #f4f4f4; padding: 2px 4px; border-radius: 4px; }}
                </style>
            </head>
            <body>
                <h1>Outlook Authentication Server</h1>
                <div class="info-box">
                    <p>This server is running to handle Microsoft Graph API authentication callbacks.</p>
                    <p>Don't navigate here directly. Instead, use the <code>authenticate</code> tool in Claude to start the authentication process.</p>
                    <p>Make sure you've set the <code>MS_CLIENT_ID</code> and <code>MS_CLIENT_SECRET</code> environment variables.</p>
                </div>
                <p>Server is running at http://localhost:3333</p>
            </body>
        </html>
    """,
}


def exchange_code_for_tokens(code: str) -> Dict:
    """Exchange authorization code for tokens"""
    import requests

    token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    token_data = {
        "client_id": settings.MS_CLIENT_ID,
        "client_secret": settings.MS_CLIENT_SECRET,
        "code": code,
        "redirect_uri": f"{settings.MS_AUTH_SERVER_URL}/auth/callback",
        "grant_type": "authorization_code",
        "scope": " ".join(settings.MS_SCOPES),
    }

    response = requests.post(token_url, data=token_data)
    result = response.json()

    if "error" in result:
        raise HTTPException(
            status_code=400,
            detail=f"Token exchange failed: {result.get('error_description', 'Unknown error')}",
        )

    # Calculate expiration time
    result["expires_at"] = int(time.time()) + result["expires_in"]

    # Save tokens to file with secure permissions
    token_path = settings.MS_TOKEN_STORE_PATH
    with open(token_path, "w") as f:
        json.dump(result, f, indent=2)

    # Set restrictive permissions (owner read/write only)
    os.chmod(token_path, TOKEN_FILE_MODE)

    logger.info(f"Tokens saved securely to {token_path}")

    return result


@app.get("/", response_class=HTMLResponse)
async def root():
    """Handle root path"""
    return TEMPLATES["root"]


@app.get("/auth")
async def auth():
    """Handle authentication request"""
    logger.info("Auth request received, redirecting to Microsoft login...")

    # Verify credentials are set
    if not settings.MS_CLIENT_ID or not settings.MS_CLIENT_SECRET:
        return HTMLResponse(
            TEMPLATES["error"].format(
                title="Configuration Error",
                content="""
                    <p>Microsoft Graph API credentials are not set. Please set the following environment variables:</p>
                    <ul>
                        <li><code>MS_CLIENT_ID</code></li>
                        <li><code>MS_CLIENT_SECRET</code></li>
                    </ul>
                """,
            ),
            status_code=500,
        )

    # Build auth parameters with secure CSRF state token
    state_token = generate_state_token()
    auth_params = {
        "client_id": settings.MS_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": f"{settings.MS_AUTH_SERVER_URL}/auth/callback",
        "scope": " ".join(settings.MS_SCOPES),
        "response_mode": "query",
        "state": state_token,  # Cryptographically secure state for CSRF protection
    }

    # Construct auth URL exactly as in the original JavaScript code
    auth_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?{urllib.parse.urlencode(auth_params)}"
    logger.info(f"Redirecting to: {auth_url}")

    # Redirect to Microsoft's login page
    return RedirectResponse(url=auth_url)


@app.get("/auth/callback", response_class=HTMLResponse)
async def auth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
):
    """Handle authentication callback with CSRF validation"""
    # Validate CSRF state token
    if state and not validate_state_token(state):
        logger.error("Invalid or expired state token - possible CSRF attack")
        return HTMLResponse(
            TEMPLATES["error"].format(
                title="Security Error",
                content="<p>Invalid or expired security token. Please try authenticating again.</p>",
            ),
            status_code=403,
        )

    if error:
        logger.error(f"Authentication error: {error} - {error_description}")
        # Escape error messages to prevent XSS
        safe_error = escape_html(error)
        safe_description = escape_html(error_description) if error_description else 'No description provided'
        return HTMLResponse(
            TEMPLATES["error"].format(
                title="Authentication Error",
                content=f"""
                    <p><strong>Error:</strong> {safe_error}</p>
                    <p><strong>Description:</strong> {safe_description}</p>
                """,
            ),
            status_code=400,
        )

    if not code:
        logger.error("No authorization code provided")
        return HTMLResponse(
            TEMPLATES["error"].format(
                title="Missing Authorization Code",
                content="<p>No authorization code was provided in the callback.</p>",
            ),
            status_code=400,
        )

    try:
        logger.info("Authorization code received, exchanging for tokens...")
        tokens = exchange_code_for_tokens(code)
        logger.info("Token exchange successful")
        return TEMPLATES["success"]
    except Exception as err:
        logger.error(f"Token exchange error: {str(err)}")
        # Escape error message to prevent XSS
        safe_error_msg = escape_html(str(err))
        return HTMLResponse(
            TEMPLATES["error"].format(
                title="Token Exchange Error", content=f"<p>{safe_error_msg}</p>"
            ),
            status_code=500,
        )


def run_server():
    """Run the authentication server"""
    logger.info("Starting Outlook Authentication Server")
    logger.info(f"Server running at http://localhost:3333")
    logger.info(
        f"Waiting for authentication callback at {settings.MS_AUTH_SERVER_URL}/auth/callback"
    )
    logger.info(f"Token will be stored at: {settings.MS_TOKEN_STORE_PATH}")

    if not settings.MS_CLIENT_ID or not settings.MS_CLIENT_SECRET:
        logger.warning("\n⚠️  WARNING: Microsoft Graph API credentials are not set.")
        logger.warning(
            "   Please set the MS_CLIENT_ID and MS_CLIENT_SECRET environment variables."
        )

    uvicorn.run(
        "outlook_auth_server:app", host="localhost", port=3333, log_level="info"
    )


if __name__ == "__main__":
    run_server()
