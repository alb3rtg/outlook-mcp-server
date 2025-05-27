"""
Outlook Authentication Server

A standalone server that handles Microsoft Graph API authentication
through OAuth 2.0 using FastAPI.
"""

import json
import time
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
import uvicorn
import urllib.parse

from config import settings
from logger import logger


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

    # Save tokens to file
    with open(settings.MS_TOKEN_STORE_PATH, "w") as f:
        json.dump(result, f, indent=2)

    logger.info(f"Tokens saved to {settings.MS_TOKEN_STORE_PATH}")

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

    # Build auth parameters exactly as in the original JavaScript code
    auth_params = {
        "client_id": settings.MS_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": f"{settings.MS_AUTH_SERVER_URL}/auth/callback",
        "scope": " ".join(settings.MS_SCOPES),
        "response_mode": "query",
        "state": str(int(time.time())),  # Simple state parameter for security
    }

    # Construct auth URL exactly as in the original JavaScript code
    auth_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?{urllib.parse.urlencode(auth_params)}"
    logger.info(f"Redirecting to: {auth_url}")

    # Redirect to Microsoft's login page
    return RedirectResponse(url=auth_url)


@app.get("/auth/callback", response_class=HTMLResponse)
async def auth_callback(
    code: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
):
    """Handle authentication callback"""
    if error:
        logger.error(f"Authentication error: {error} - {error_description}")
        return HTMLResponse(
            TEMPLATES["error"].format(
                title="Authentication Error",
                content=f"""
                    <p><strong>Error:</strong> {error}</p>
                    <p><strong>Description:</strong> {error_description or 'No description provided'}</p>
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
    except Exception as error:
        logger.error(f"Token exchange error: {str(error)}")
        return HTMLResponse(
            TEMPLATES["error"].format(
                title="Token Exchange Error", content=f"<p>{str(error)}</p>"
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
