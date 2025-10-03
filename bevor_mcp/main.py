"""Main entry point for the Bevor MCP server."""

from fastmcp import FastMCP

mcp = FastMCP("Bevor MCP")

@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

def main():
    """Main entry point for the MCP server."""
    mcp.run()

if __name__ == "__main__":
    main()
