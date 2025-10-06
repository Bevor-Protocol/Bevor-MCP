"""Main entry point for the Bevor MCP server."""

from fastmcp import FastMCP, Context
import asyncio
import os
import sys
from pathlib import Path
from bevor_api.client import BevorApiClient

# Use fallback import explicitly for Cursor execution context
from utils.solidity_etl import find_contracts_folder_in_directory

mcp = FastMCP("Bevor MCP")

# Resolve project path safely (default to current working directory)
_env_project_path = os.getenv("PROJECT_PATH")
_resolved_project_path = _env_project_path or os.getcwd()
_contracts_folder = None
try:
    _contracts_folder = find_contracts_folder_in_directory(Path(_resolved_project_path))
except Exception:
    _contracts_folder = None

import asyncio as _asyncio
client = BevorApiClient(
    bevor_api_key=os.getenv("BEVOR_API_KEY"),
    project_id=os.getenv("PROJECT_ID"),
    contracts_folder_path=_contracts_folder,
)

_init_lock = _asyncio.Lock()
_initialized = False
initialized_client = None

async def _ensure_client_initialized_async() -> None:
    global _initialized
    global initialized_client
    if _initialized:
        return
    async with _init_lock:
        if _initialized:
            return
        # Create a separate initialized client instance
        initialized_client = await client.create()
        _initialized = True

@mcp.resource("resource://health_check")
async def health_check() -> dict:
    """Health check resource for the Bevor MCP server."""
    project_path = _resolved_project_path

    await _ensure_client_initialized_async()
    # Use the initialized client if available
    c = initialized_client or client
    bevor_api_healthy = all([
        c.project_id is not None,
        c.version_mapping_id is not None,
        c.chat_id is not None
    ])

    status = "healthy" if bevor_api_healthy else "bevor_api_unhealthy"
    status = "healthy"

    return {
        "status": status,
        "server": "Bevor MCP",
        "version": "0.1.0", 
        "uptime": "running",
        "tools_available": ["add", "audit_log"],
        "resources_available": ["health_check"],
        "contracts_folder_path": _contracts_folder,
        "bevor_api": {
            "healthy": bevor_api_healthy,
            "project_path": project_path,
            "contracts_folder_path": c.contracts_folder_path,
            "project_id": c.project_id,
            "version_mapping_id": c.version_mapping_id,
            "chat_id": c.chat_id
        }
    }

@mcp.tool
async def chat(message: str, ctx: Context) -> dict:
    """Send a chat message to the Bevor API and return the response."""
    await _ensure_client_initialized_async()
    
    # Use the initialized client if available
    c = initialized_client or client
    
    # Report starting chat
    ctx.report_progress(25, "Starting chat...")
    
    # Call chat_contract with the message
    response = c.chat_contract(message)
    
    # Report chat in progress
    ctx.report_progress(75, "Processing response...")
    
    # Report completion
    ctx.report_progress(100, "Chat complete")
    
    return response


def main():
    """Main entry point for the MCP server."""
    mcp.run()

if __name__ == "__main__":
    main()
