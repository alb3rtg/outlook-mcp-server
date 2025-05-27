# Outlook MCP Python

A Python-based Microsoft Outlook integration using Microsoft Graph API, built with FastAPI and MCP framework.

## Overview

This project provides a server implementation for Microsoft Outlook integration using the Microsoft Graph API. It includes authentication handling, mail operations, and various utility functions for working with Outlook data.

## Features

- Microsoft Graph API integration
- OAuth2 authentication flow
- Mail operations (send, read, manage)
- FastAPI-based server implementation
- Environment-based configuration
- Logging functionality

## Project Structure

- `auth/` - Authentication related modules
- `mail/` - Mail operation modules
- `utils/` - Utility functions
- `main.py` - Main application entry point
- `server.py` - Server configuration
- `config.py` - Configuration settings
- `logger.py` - Logging configuration
- `outlook_auth_server.py` - Outlook authentication server implementation

## Prerequisites

- Python 3.8 or higher
- Microsoft Azure account with registered application
- Microsoft Graph API access

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd mcp-outlook-python
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Azure App Registration & Configuration

To use this MCP server you need to first register and configure an app in Azure Portal. The following steps will take you through the process of registering a new app, configuring its permissions, and generating a client secret.

### App Registration

1. Open [Azure Portal](https://portal.azure.com/) in your browser
2. Sign in with a Microsoft Work or Personal account
3. Search for or cilck on "App registrations"
4. Click on "New registration"
5. Enter a name for the app, for example "Outlook MCP Server"
6. Select the "Accounts in any organizational directory and personal Microsoft accounts" option
7. In the "Redirect URI" section, select "Web" from the dropdown and enter "http://localhost:3333/auth/callback" in the textbox
8. Click on "Register"
9. From the Overview section of the app settings page, copy the "Application (client) ID" and enter it as the MS_CLIENT_ID in the .env file as well as the OUTLOOK_CLIENT_ID in the claude-config-sample.json file

### App Permissions

1. From the app settings page in Azure Portal select the "API permissions" option under the Manage section
2. Click on "Add a permission"
3. Click on "Microsoft Graph"
4. Select "Delegated permissions"
5. Search for the following permissions and slect the checkbox next to each one
    - offline_access
    - User.Read
    - Mail.Read
    - Mail.Send
    - Calendars.Read
    - Calendars.ReadWrite
    - Contacts.Read
6. Click on "Add permissions"

### Client Secret

1. From the app settings page in Azure Portal select the "Certificates & secrets" option under the Manage section
2. Switch to the "Client secrets" tab
3. Click on "New client secret"
4. Enter a description, for example "Client Secret"
5. Select the longest possible expiration time
6. Click on "Add"
7. Copy the secret value and enter it as the MS_CLIENT_SECRET in the .env file as well as the OUTLOOK_CLIENT_SECRET in the claude-config-sample.json file

## Configuration

1. Create a `.env` file in the root directory with the following variables:
```
MS_CLIENT_ID=your-ms-client-id
MS_CLIENT_SECRET=your-ms-client-secret
MS_AUTH_SERVER_URL=your-ms-auth-server-url
```

2. Update the configuration in `config.py` as needed.

## Usage with Claude Desktop

1. Copy the sample configuration from `claude-config-sample.json` to your Claude Desktop configuration
2. Restart Claude Desktop
3. Authenticate with Microsoft using the `authenticate` tool
4. Use the email tools to manage your Outlook account


## Authentication Flow

1. Start a local authentication server on port 3333 (using `outlook-auth-server.js`)
2. Use the `authenticate` tool to get an authentication URL
3. Complete the authentication in your browser
4. Tokens are stored in `~/.outlook-mcp-tokens.json`

## Troubleshooting

- **Authentication Issues**: Check the token file and authentication server logs
- **API Call Failures**: Check for detailed error messages in the response

## Dependencies

- fastapi
- uvicorn
- python-dotenv
- pydantic
- pydantic-settings
- requests
- aiohttp
- mcp
