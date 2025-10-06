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

client = BevorApiClient(
    bevor_api_key=os.getenv("BEVOR_API_KEY"),
    project_id=os.getenv("PROJECT_ID"),
    contracts_folder_path=_contracts_folder,
).create()

@mcp.resource("resource://health_check")
def health_check() -> dict:
    """Health check resource for the Bevor MCP server."""
    project_path = _resolved_project_path

    bevor_api_healthy = all([
        client.project_id is not None,
        client.version_mapping_id is not None,
        client.chat_id is not None
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
            "contracts_folder_path": client.contracts_folder_path,
            "project_id": client.project_id,
            "version_mapping_id": client.version_mapping_id,
            "chat_id": client.chat_id
        }
    }

@mcp.tool
async def process_items(items: list[str], ctx: Context) -> dict:
    """Process a list of items with progress updates."""
    total = len(items)
    results = []
    
    for i, item in enumerate(items):
        # Report progress as we process each item
        await ctx.report_progress(progress=i, total=total)
        
        # Simulate processing time
        await asyncio.sleep(0.1)
        results.append(item.upper())
    
    # Report 100% completion
    await ctx.report_progress(progress=total, total=total)
    
    return {"processed": len(results), "results": results}


def main():
    """Main entry point for the MCP server."""
    mcp.run()

if __name__ == "__main__":
    main()
