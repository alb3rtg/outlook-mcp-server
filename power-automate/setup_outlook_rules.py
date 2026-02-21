#!/usr/bin/env python3
"""
Set up Outlook Rules for Promotional Email Management
Uses Microsoft Graph API with existing tokens
"""

import json
import requests
import os
from datetime import datetime

# Load tokens
TOKEN_FILE = os.path.expanduser("~/.outlook-mcp-tokens.json")

def load_tokens():
    with open(TOKEN_FILE, 'r') as f:
        return json.load(f)

def refresh_token_if_needed(tokens):
    """Refresh access token if expired"""
    if tokens.get('expires_at', 0) < datetime.now().timestamp():
        print("Token expired, attempting refresh...")
        # Would need client_id/secret to refresh - skip for now
        return tokens
    return tokens

def graph_api_call(method, endpoint, tokens, data=None):
    """Make a Microsoft Graph API call"""
    headers = {
        'Authorization': f"Bearer {tokens['access_token']}",
        'Content-Type': 'application/json'
    }
    url = f"https://graph.microsoft.com/v1.0/{endpoint}"

    if method == 'GET':
        response = requests.get(url, headers=headers)
    elif method == 'POST':
        response = requests.post(url, headers=headers, json=data)
    elif method == 'PATCH':
        response = requests.patch(url, headers=headers, json=data)

    return response

def list_folders(tokens):
    """List existing mail folders"""
    print("\n📁 Checking existing folders...")
    response = graph_api_call('GET', 'me/mailFolders?$top=50', tokens)

    if response.status_code == 200:
        folders = response.json().get('value', [])
        print(f"   Found {len(folders)} folders:")
        for f in folders:
            print(f"   - {f['displayName']} ({f.get('totalItemCount', 0)} emails)")
        return folders
    else:
        print(f"   ❌ Error: {response.status_code} - {response.text}")
        return []

def create_folder(tokens, folder_name):
    """Create a new mail folder"""
    print(f"\n📁 Creating folder '{folder_name}'...")

    data = {
        "displayName": folder_name
    }

    response = graph_api_call('POST', 'me/mailFolders', tokens, data)

    if response.status_code == 201:
        folder = response.json()
        print(f"   ✅ Created folder '{folder_name}' (ID: {folder['id'][:20]}...)")
        return folder
    elif response.status_code == 409:
        print(f"   ⚠️ Folder '{folder_name}' already exists")
        # Find and return existing folder
        folders = list_folders(tokens)
        for f in folders:
            if f['displayName'].lower() == folder_name.lower():
                return f
        return None
    else:
        print(f"   ❌ Error: {response.status_code}")
        error = response.json() if response.text else {}
        print(f"   Message: {error.get('error', {}).get('message', response.text)}")
        return None

def list_rules(tokens):
    """List existing inbox rules"""
    print("\n📋 Checking existing rules...")
    response = graph_api_call('GET', 'me/mailFolders/inbox/messageRules', tokens)

    if response.status_code == 200:
        rules = response.json().get('value', [])
        print(f"   Found {len(rules)} existing rules:")
        for r in rules:
            print(f"   - {r['displayName']} (enabled: {r.get('isEnabled', False)})")
        return rules
    else:
        print(f"   ❌ Error: {response.status_code} - {response.text[:200]}")
        return []

def create_rule(tokens, rule_name, folder_id, conditions):
    """Create an inbox rule"""
    print(f"\n📋 Creating rule '{rule_name}'...")

    data = {
        "displayName": rule_name,
        "sequence": 1,
        "isEnabled": True,
        "conditions": conditions,
        "actions": {
            "moveToFolder": folder_id,
            "markAsRead": True,
            "stopProcessingRules": True
        }
    }

    response = graph_api_call('POST', 'me/mailFolders/inbox/messageRules', tokens, data)

    if response.status_code == 201:
        rule = response.json()
        print(f"   ✅ Created rule '{rule_name}'")
        return rule
    else:
        print(f"   ❌ Error: {response.status_code}")
        error = response.json() if response.text else {}
        print(f"   Message: {error.get('error', {}).get('message', response.text[:200])}")
        return None

def search_promotional_emails(tokens):
    """Search for promotional emails to show what would be caught"""
    print("\n🔍 Searching for promotional emails in inbox...")

    search_query = "unsubscribe"
    response = graph_api_call(
        'GET',
        f"me/messages?$filter=contains(body/content,'{search_query}')&$top=10&$select=from,subject,receivedDateTime",
        tokens
    )

    if response.status_code == 200:
        emails = response.json().get('value', [])
        print(f"   Found {len(emails)} emails containing 'unsubscribe' (showing first 10):")
        for e in emails[:10]:
            sender = e.get('from', {}).get('emailAddress', {}).get('address', 'unknown')
            subject = e.get('subject', 'No subject')[:50]
            print(f"   - {sender}: {subject}...")
        return emails
    else:
        print(f"   ❌ Error: {response.status_code}")
        return []

def count_inbox_emails(tokens):
    """Count total emails in inbox"""
    print("\n📊 Counting inbox emails...")
    response = graph_api_call('GET', 'me/mailFolders/inbox', tokens)

    if response.status_code == 200:
        folder = response.json()
        total = folder.get('totalItemCount', 0)
        unread = folder.get('unreadItemCount', 0)
        print(f"   Total: {total:,} emails")
        print(f"   Unread: {unread:,} emails")
        return total
    return 0

def main():
    print("=" * 60)
    print("OUTLOOK RULES SETUP")
    print("=" * 60)
    print(f"Account: albert.greenberg@hotmail.com")

    # Load tokens
    tokens = load_tokens()
    print(f"Token expires: {datetime.fromtimestamp(tokens.get('expires_at', 0))}")
    print(f"Scopes: {tokens.get('scope', 'unknown')}")

    # Check current state
    count_inbox_emails(tokens)
    folders = list_folders(tokens)

    # Check if folder exists
    promo_folder = None
    for f in folders:
        if f['displayName'].lower() == 'promotional-todelete':
            promo_folder = f
            print(f"\n✅ Folder 'Promotional-ToDelete' already exists")
            break

    # Create folder if needed
    if not promo_folder:
        promo_folder = create_folder(tokens, "Promotional-ToDelete")

    if not promo_folder:
        print("\n❌ Could not create or find folder. Checking permissions...")
        print("   Required scope: Mail.ReadWrite")
        print(f"   Current scopes: {tokens.get('scope', 'unknown')}")
        return False

    # List existing rules
    existing_rules = list_rules(tokens)

    # Create rules for promotional emails
    rule_exists = any(r['displayName'] == 'Move Promotional Emails' for r in existing_rules)

    if not rule_exists:
        # Rule: Move emails containing "unsubscribe" to promotional folder
        rule1 = create_rule(
            tokens,
            "Move Promotional Emails",
            promo_folder['id'],
            {
                "bodyContains": ["unsubscribe", "unsubscribe from this list", "email preferences"]
            }
        )

        if not rule1:
            print("\n❌ Could not create rule. Checking permissions...")
            print("   Required scope: MailboxSettings.ReadWrite")
            print(f"   Current scopes: {tokens.get('scope', 'unknown')}")
    else:
        print("\n✅ Rule 'Move Promotional Emails' already exists")

    # Show sample of what would be caught
    search_promotional_emails(tokens)

    print("\n" + "=" * 60)
    print("SETUP COMPLETE")
    print("=" * 60)

    return True

if __name__ == '__main__':
    main()
