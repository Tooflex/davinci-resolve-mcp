"""
DaVinci Resolve MCP Server

This module implements a Model Context Protocol (MCP) server for DaVinci Resolve,
allowing AI assistants to interact with DaVinci Resolve through the MCP protocol.
"""

import logging
import sys
from typing import List

# Add MCP library to path if not installed as a package
try:
    from mcp.server.fastmcp import FastMCP
    print("Successfully imported FastMCP", file=sys.stderr)
except ImportError as e:
    print(f"Error importing FastMCP: {e}", file=sys.stderr)
    raise

# Import ResolveAPI (assumes resolve_api.py is in the same directory or installed)
try:
    from resolve_api import ResolveAPI
    print("Successfully imported ResolveAPI", file=sys.stderr)
except ImportError as e:
    print(f"Error importing ResolveAPI: {e}", file=sys.stderr)
    raise

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("resolve_mcp")

# Create the MCP server
mcp = FastMCP("DaVinci Resolve")

# Initialize the Resolve API
resolve_api = ResolveAPI()

# Check connection to Resolve
if not resolve_api.is_connected():
    logger.error("Failed to connect to DaVinci Resolve. Ensure it is running.")
else:
    logger.info("Successfully connected to DaVinci Resolve.")

# --- Resource Definitions ---

@mcp.resource("system://status")
def get_system_status() -> str:
    """Get the current status of the DaVinci Resolve connection."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    project_name = resolve_api.get_project_name() or "No project open"
    timeline = resolve_api.get_current_timeline()
    timeline_name = timeline.GetName() if timeline else "No timeline open"
    return f"Connected: Yes\nProject: {project_name}\nTimeline: {timeline_name}"

@mcp.resource("project://current")
def get_current_project() -> str:
    """Get information about the current project."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    project = resolve_api.get_current_project()
    if not project:
        return "No project open."
    return f"Name: {project.GetName()}\nTimelines: {project.GetTimelineCount()}"

@mcp.resource("timeline://current")
def get_current_timeline() -> str:
    """Get information about the current timeline."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    timeline = resolve_api.get_current_timeline()
    if not timeline:
        return "No timeline open."
    return (f"Name: {timeline.GetName()}\n"
            f"Duration: {timeline.GetEndFrame() - timeline.GetStartFrame() + 1} frames\n"
            f"Video Tracks: {timeline.GetTrackCount('video')}")

@mcp.resource("mediapool://current")
def get_current_media_pool_folder() -> str:
    """Get information about the current media pool folder."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    media_pool = resolve_api.get_media_pool()
    if not media_pool:
        return "No media pool available."
    folder = media_pool.GetCurrentFolder()
    if not folder:
        return "No current folder."
    clips = folder.GetClips()
    clip_count = len(clips) if clips else 0
    return f"Folder: {folder.GetName()}\nClips: {clip_count}"

# --- Tool Definitions ---

@mcp.tool()
def create_project(name: str) -> str:
    """Create a new project in DaVinci Resolve."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    success = resolve_api.create_project(name)
    return f"Project '{name}' created." if success else f"Failed to create '{name}'."

@mcp.tool()
def load_project(name: str) -> str:
    """Load an existing project in DaVinci Resolve."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    success = resolve_api.load_project(name)
    return f"Project '{name}' loaded." if success else f"Failed to load '{name}'."

@mcp.tool()
def create_timeline(name: str) -> str:
    """Create a new timeline in the current project."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    success = resolve_api.create_timeline(name)
    return f"Timeline '{name}' created." if success else f"Failed to create '{name}'."

@mcp.tool()
def import_media(file_paths: List[str]) -> str:
    """Import media files into the current media pool folder."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    clips = resolve_api.add_items_to_media_pool(file_paths)
    return f"Imported {len(clips)} files." if clips else "Failed to import files."

@mcp.tool()
def open_page(page_name: str) -> str:
    """Open a specific page in DaVinci Resolve."""
    valid_pages = ["media", "edit", "fusion", "color", "fairlight", "deliver"]
    if page_name.lower() not in valid_pages:
        return f"Invalid page. Use: {', '.join(valid_pages)}"
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    success = resolve_api.open_page(page_name.lower())
    return f"Opened '{page_name}' page." if success else f"Failed to open '{page_name}'."

# --- Main Entry Point ---

def main():
    """Run the MCP server."""
    logger.info("Starting DaVinci Resolve MCP server...")
    mcp.run()

if __name__ == "__main__":
    main()