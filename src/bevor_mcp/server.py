"""Main entry point for the Bevor MCP server."""

from fastmcp import FastMCP, Context
import asyncio
import os

mcp = FastMCP("Bevor MCP")


@mcp.resource("resource://health_check")
def health_check() -> dict:
    """Health check resource for the Bevor MCP server."""
    project_path = os.getenv("PROJECT_PATH")

    return {
        "status": "healthy",
        "server": "Bevor MCP",
        "version": "0.1.0",
        "uptime": "running",
        "tools_available": ["add", "audit_log"],
        "resources_available": ["health_check"],
        "project_path": project_path
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


@mcp.tool
def audit_log(action: str, user: str = "system", details: str = "") -> dict:
    """Create an audit log entry for tracking actions and events."""
    import datetime
    
    audit_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "action": action,
        "user": user,
        "details": details,
        "status": "logged"
    }
    
    # In a real implementation, you'd save this to a database or log file
    print(f"AUDIT: {audit_entry}")
    
    return audit_entry


def main():
    """Main entry point for the MCP server."""
    import sys
    
    # Check if we should run interactive chat
    if len(sys.argv) > 1 and sys.argv[1] == "chat":
        interactive_chat()
    else:
        mcp.run()

if __name__ == "__main__":
    main()
