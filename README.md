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

## Configuration

1. Create a `.env` file in the root directory with the following variables:
```
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
REDIRECT_URI=your_redirect_uri
```

2. Update the configuration in `config.py` as needed.

## Usage

1. Start the server:
```bash
python main.py
```

2. The server will start and be available at the configured port (default: 8000).

## Project Structure

- `auth/` - Authentication related modules
- `mail/` - Mail operation modules
- `utils/` - Utility functions
- `main.py` - Main application entry point
- `server.py` - Server configuration
- `config.py` - Configuration settings
- `logger.py` - Logging configuration
- `outlook_auth_server.py` - Outlook authentication server implementation

## Dependencies

- fastapi
- uvicorn
- python-dotenv
- pydantic
- pydantic-settings
- requests
- aiohttp
- mcp
