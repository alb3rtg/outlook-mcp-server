from server import mcp
from auth.tools import *
from mail.tools import *

if __name__ == "__main__":
    print("Starting Outlook MCP Server (Graph API)...")
    mcp.run()
