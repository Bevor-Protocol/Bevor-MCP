"""Main entry point for the Bevor MCP server."""

from fastmcp import FastMCP

mcp = FastMCP("Bevor MCP")


@mcp.resource
def health_check() -> dict:
    """Health check resource for the Bevor MCP server."""
    return {
        "status": "healthy",
        "server": "Bevor MCP",
        "version": "0.1.0",
        "uptime": "running",
        "tools_available": ["add", "audit_log"],
        "resources_available": ["health_check"]
    }

@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


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
    mcp.run()

if __name__ == "__main__":
    main()
