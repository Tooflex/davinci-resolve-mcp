"""
DaVinci Resolve MCP Server

This module implements a Model Context Protocol (MCP) server for DaVinci Resolve,
allowing AI assistants to interact with DaVinci Resolve through the MCP protocol.
"""

import logging
import sys
from typing import List, Dict, Any, Optional

# Configure logging with timestamp, name, level, and message format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("resolve_mcp")  # Logger instance for this module

# Add MCP library to path if not installed as a package
try:
    from mcp.server.fastmcp import FastMCP  # Import FastMCP for MCP server functionality
    print("Successfully imported FastMCP", file=sys.stderr)
except ImportError as e:
    print(f"Error importing FastMCP: {e}", file=sys.stderr)
    raise  # Raise exception if MCP library is unavailable

# Import ResolveAPI (assumes resolve_api.py is in the same directory or installed)
try:
    from resolve_api import ResolveAPI  # Import ResolveAPI for DaVinci Resolve interaction
    print("Successfully imported ResolveAPI", file=sys.stderr)
except ImportError as e:
    print(f"Error importing ResolveAPI: {e}", file=sys.stderr)
    raise  # Raise exception if ResolveAPI is unavailable

# Create the MCP server instance with the name "DaVinci Resolve"
mcp = FastMCP("DaVinci Resolve")

# Initialize the Resolve API to connect to DaVinci Resolve
resolve_api = ResolveAPI()

# Check connection to Resolve and log the result
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

@mcp.resource("gallery://albums")
def get_gallery_albums() -> str:
    """Get a list of albums in the gallery."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    albums = resolve_api.get_gallery_albums()
    return "\n".join([album.GetName() for album in albums]) if albums else "No albums"

@mcp.resource("timeline://items")
def get_timeline_items_resource() -> str:
    """Get a list of items in the first video track of the current timeline."""
    items = resolve_api.get_timeline_items("video", 1)
    return "\n".join([f"Clip {i+1}: {item.GetName()}" for i, item in enumerate(items)]) if items else "No items"

# --- Tool Definitions ---

@mcp.tool()
def refresh() -> str:
    """Refresh all internal Resolve objects to reflect the current state."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    resolve_api.refresh()
    return "Resolve API state refreshed."

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
def save_project() -> str:
    """Save the current project."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    success = resolve_api.save_project()
    return "Project saved." if success else "Failed to save project."

@mcp.tool()
def export_project(project_name: str, file_path: str) -> str:
    """Export a project to a file."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    success = resolve_api.export_project(project_name, file_path)
    return f"Project '{project_name}' exported to '{file_path}'." if success else "Failed to export project."

@mcp.tool()
def import_project(file_path: str) -> str:
    """Import a project from a file."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    success = resolve_api.import_project(file_path)
    return f"Project imported from '{file_path}'." if success else "Failed to import project."

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

@mcp.tool()
def create_timeline(name: str) -> str:
    """Create a new timeline in the current project."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    success = resolve_api.create_timeline(name)
    return f"Timeline '{name}' created." if success else f"Failed to create '{name}'."

@mcp.tool()
def set_current_timeline(timeline_index: int) -> str:
    """Set the specified timeline as the current one by 1-based index."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    timeline = resolve_api.get_timeline_by_index(timeline_index)
    if not timeline:
        return f"No timeline found at index {timeline_index}."
    success = resolve_api.set_current_timeline(timeline)
    return f"Timeline at index {timeline_index} set as current." if success else "Failed to set timeline."

@mcp.tool()
def import_media(file_paths: List[str]) -> str:
    """Import media files into the current media pool folder."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    clips = resolve_api.add_items_to_media_pool(file_paths)
    return f"Imported {len(clips)} files." if clips else "Failed to import files."

@mcp.tool()
def add_sub_folder(parent_folder_name: str, folder_name: str) -> str:
    """Add a subfolder to the specified parent folder in the media pool."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    media_pool = resolve_api.get_media_pool()
    if not media_pool:
        return "No media pool available."
    root_folder = media_pool.GetRootFolder()
    parent_folder = next((f for f in root_folder.GetSubFolders() if f.GetName() == parent_folder_name), None)
    if not parent_folder:
        return f"Parent folder '{parent_folder_name}' not found."
    sub_folder = resolve_api.add_sub_folder(parent_folder, folder_name)
    return f"Subfolder '{folder_name}' added to '{parent_folder_name}'." if sub_folder else "Failed to add subfolder."

@mcp.tool()
def append_to_timeline(clip_names: List[str]) -> str:
    """Append clips to the current timeline by name."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    media_pool = resolve_api.get_media_pool()
    if not media_pool:
        return "No media pool available."
    folder = media_pool.GetCurrentFolder()
    clips = [clip for clip in folder.GetClips() if clip.GetClipProperty("Clip Name") in clip_names]
    success = resolve_api.append_to_timeline(clips)
    return f"Appended {len(clips)} clips to timeline." if success else "Failed to append clips."

@mcp.tool()
def create_timeline_from_clips(timeline_name: str, clip_names: List[str]) -> str:
    """Create a new timeline from the specified clips by name."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    media_pool = resolve_api.get_media_pool()
    if not media_pool:
        return "No media pool available."
    folder = media_pool.GetCurrentFolder()
    clips = [clip for clip in folder.GetClips() if clip.GetClipProperty("Clip Name") in clip_names]
    timeline = resolve_api.create_timeline_from_clips(timeline_name, clips)
    return f"Timeline '{timeline_name}' created with {len(clips)} clips." if timeline else "Failed to create timeline."

@mcp.tool()
def import_timeline_from_file(file_path: str) -> str:
    """Import a timeline from a file (e.g., XML, EDL)."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    timeline = resolve_api.import_timeline_from_file(file_path)
    return f"Timeline imported from '{file_path}'." if timeline else "Failed to import timeline."

@mcp.tool()
def execute_lua(script: str) -> str:
    """Execute a Lua script in Resolve's Fusion environment."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    result = resolve_api.execute_lua(script)
    return f"Lua script executed: {result}" if result else "Failed to execute Lua script."

@mcp.tool()
def create_fusion_node(node_type: str, inputs: Dict[str, Any] = None) -> str:
    """Create a new node in the current Fusion composition."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    comp = resolve_api.get_current_comp()
    if not comp:
        return "No current Fusion composition."
    node = resolve_api.create_fusion_node(comp, node_type, inputs)
    return f"Node '{node_type}' created." if node else f"Failed to create '{node_type}' node."

@mcp.tool()
def set_clip_property(clip_name: str, property_name: str, value: Any) -> str:
    """Set a property on a timeline clip by name."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    items = resolve_api.get_timeline_items("video", 1)
    clip = next((item for item in items if item.GetName() == clip_name), None)
    if not clip:
        return f"Clip '{clip_name}' not found."
    success = resolve_api.set_clip_property(clip, property_name, value)
    return f"Property '{property_name}' set to {value} on '{clip_name}'." if success else "Failed to set property."

@mcp.tool()
def add_color_node(node_type: str = "Corrector") -> str:
    """Add a new node to the current clip's color grade."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    node = resolve_api.add_color_node(node_type)
    return f"Color node '{node_type}' added." if node else "Failed to add color node."

@mcp.tool()
def set_project_setting(key: str, value: Any) -> str:
    """Set a specific project setting."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    success = resolve_api.set_project_setting(key, value)
    return f"Project setting '{key}' set to {value}." if success else f"Failed to set '{key}'."

@mcp.tool()
def start_project_render(preset_name: str = None, render_path: str = None) -> str:
    """Start rendering the current project with optional preset and path."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    success = resolve_api.start_render(preset_name, render_path)
    return "Render started." if success else "Failed to start render."

@mcp.tool()
def add_timeline_marker(frame: int, color: str = "Blue", name: str = "", note: str = "") -> str:
    """Add a marker to the current timeline at a specific frame."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    success = resolve_api.add_timeline_marker(frame, color, name, note)
    return f"Marker added at frame {frame}." if success else "Failed to add marker."

@mcp.tool()
def save_still(album_name: str = "Stills") -> str:
    """Save the current clip's grade as a still in the specified gallery album."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    still = resolve_api.save_still(album_name)
    return f"Still saved to '{album_name}'." if still else "Failed to save still."

@mcp.tool()
def apply_still(still_name: str, clip_name: str = None) -> str:
    """Apply a still (grade) to a clip by name, defaulting to current clip if none specified."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    gallery = resolve_api.get_gallery()
    if not gallery:
        return "No gallery available."
    albums = resolve_api.get_gallery_albums()
    still = None
    for album in albums:
        stills = album.GetStills()
        still = next((s for s in stills if s.GetLabel() == still_name), None)
        if still:
            break
    if not still:
        return f"Still '{still_name}' not found."
    clip = None
    if clip_name:
        items = resolve_api.get_timeline_items("video", 1)
        clip = next((item for item in items if item.GetName() == clip_name), None)
        if not clip:
            return f"Clip '{clip_name}' not found."
    success = resolve_api.apply_still(still, clip)
    return f"Still '{still_name}' applied." if success else "Failed to apply still."

@mcp.tool()
def add_track(track_type: str = "video") -> str:
    """Add a new track to the current timeline."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    success = resolve_api.add_track(track_type)
    return f"{track_type.capitalize()} track added." if success else f"Failed to add {track_type} track."

@mcp.tool()
def set_track_name(track_type: str, track_index: int, name: str) -> str:
    """Set the name of a track in the current timeline."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    success = resolve_api.set_track_name(track_type, track_index, name)
    return f"Track {track_index} named '{name}'." if success else "Failed to set track name."

@mcp.tool()
def enable_track(track_type: str, track_index: int, enable: bool = True) -> str:
    """Enable or disable a track in the current timeline."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    success = resolve_api.enable_track(track_type, track_index, enable)
    state = "enabled" if enable else "disabled"
    return f"Track {track_index} {state}." if success else f"Failed to {state} track."

@mcp.tool()
def set_audio_volume(clip_name: str, volume: float) -> str:
    """Set the audio volume of a timeline clip by name."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    items = resolve_api.get_timeline_items("audio", 1)
    clip = next((item for item in items if item.GetName() == clip_name), None)
    if not clip:
        return f"Clip '{clip_name}' not found."
    success = resolve_api.set_audio_volume(clip, volume)
    return f"Volume set to {volume} on '{clip_name}'." if success else "Failed to set volume."

@mcp.tool()
def set_track_volume(track_index: int, volume: float) -> str:
    """Set the volume of an audio track in the current timeline."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    success = resolve_api.set_track_volume(track_index, volume)
    return f"Track {track_index} volume set to {volume}." if success else "Failed to set track volume."

@mcp.tool()
def set_current_version(clip_name: str, version_index: int, version_type: str = "color") -> str:
    """Set the current version for a clip by name (e.g., switch between color grades)."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    items = resolve_api.get_timeline_items("video", 1)
    clip = next((item for item in items if item.GetName() == clip_name), None)
    if not clip:
        return f"Clip '{clip_name}' not found."
    success = resolve_api.set_current_version(clip, version_index, version_type)
    return f"Version {version_index} set for '{clip_name}'." if success else "Failed to set version."

@mcp.tool()
def play_timeline() -> str:
    """Start playback in the current timeline."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    success = resolve_api.play()
    return "Playback started." if success else "Failed to start playback."

@mcp.tool()
def stop_timeline() -> str:
    """Stop playback in the current timeline."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    success = resolve_api.stop()
    return "Playback stopped." if success else "Failed to stop playback."

@mcp.tool()
def set_playhead_position(frame: int) -> str:
    """Set the playhead position to a specific frame in the current timeline."""
    if not resolve_api.is_connected():
        return "Not connected to DaVinci Resolve."
    success = resolve_api.set_playhead_position(frame)
    return f"Playhead set to frame {frame}." if success else "Failed to set playhead position."

# --- Main Entry Point ---

def main():
    """Run the MCP server."""
    logger.info("Starting DaVinci Resolve MCP server...")
    mcp.run()  # Start the MCP server to listen for connections

if __name__ == "__main__":
    main()  # Execute main function if script is run directly