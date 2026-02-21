#!/usr/bin/env python3
"""Refresh Outlook access token"""

import json
import requests
import os
from datetime import datetime

TOKEN_FILE = os.path.expanduser("~/.outlook-mcp-tokens.json")
CLIENT_ID = os.environ.get("MS_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("MS_CLIENT_SECRET", "")

def refresh_tokens():
    with open(TOKEN_FILE, 'r') as f:
        tokens = json.load(f)

    print(f"Current token expires: {datetime.fromtimestamp(tokens.get('expires_at', 0))}")
    print(f"Refreshing token...")

    # Request new token using refresh token
    response = requests.post(
        'https://login.microsoftonline.com/consumers/oauth2/v2.0/token',
        data={
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'refresh_token': tokens['refresh_token'],
            'grant_type': 'refresh_token',
            'scope': 'User.Read Mail.Read Mail.ReadWrite Mail.Send MailboxSettings.ReadWrite offline_access'
        }
    )

    if response.status_code == 200:
        new_tokens = response.json()
        new_tokens['expires_at'] = datetime.now().timestamp() + new_tokens.get('expires_in', 3600)

        # Save new tokens
        with open(TOKEN_FILE, 'w') as f:
            json.dump(new_tokens, f, indent=2)

        print(f"✅ Token refreshed successfully!")
        print(f"New expiry: {datetime.fromtimestamp(new_tokens['expires_at'])}")
        print(f"New scopes: {new_tokens.get('scope', 'unknown')}")
        return True
    else:
        print(f"❌ Failed to refresh: {response.status_code}")
        print(response.text)
        return False

if __name__ == '__main__':
    refresh_tokens()
