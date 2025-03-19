Here’s an updated version of the README with enhancements reflecting the expanded functionality of the `ResolveAPI` class, improved clarity, and additional details for setup and usage. The structure remains consistent with your original README, but I’ve incorporated the new features (e.g., gallery management, track control, audio adjustments, playback, etc.) and refined the instructions for `uv` installation and Claude integration.

---

# DaVinci Resolve MCP Server

A Model Context Protocol (MCP) server that enables AI assistants like Claude to interact with DaVinci Resolve Studio, providing advanced control over editing, color grading, audio, and more.

## Overview

This server implements the MCP protocol to create a bridge between AI assistants and DaVinci Resolve. It allows AI assistants to:

- Create, load, and manage DaVinci Resolve projects
- Manipulate timelines, tracks, and clips
- Import and organize media files
- Access and modify Fusion compositions
- Perform color grading and manage stills in the Gallery
- Adjust audio settings and control playback
- Navigate between Resolve pages (Media, Edit, Fusion, Color, Fairlight, Deliver)
- Execute custom Python and Lua scripts
- Export and import projects

## Requirements

- DaVinci Resolve Studio 18.0 or newer
- Python 3.10 or newer
- Access to the DaVinci Resolve scripting API

## Installation with uv

[uv](https://github.com/astral-sh/uv) is a fast, modern Python package installer and resolver that outperforms pip. Follow these steps to install and set up the DaVinci Resolve MCP server using `uv`:

### 1. Install uv

If `uv` is not installed:

```bash
# Using pip (ensure pip is for Python 3.10+)
pip install uv

# Using Homebrew (macOS)
brew install uv

# Using Conda
conda install -c conda-forge uv
```

Verify installation:

```bash
uv --version
```

### 2. Create a Virtual Environment

Create and activate a virtual environment to isolate dependencies:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install the DaVinci Resolve MCP Server

Install the server and its dependencies from the project directory:

```bash
# From the project directory (editable install for development)
uv install -e .

# Or directly from GitHub (replace with your repo URL)
uv install git+https://github.com/yourusername/davinci-resolve-mcp.git
```

### 4. Install Dependencies

Ensure `requirements.txt` includes:

```
mcp
pydantic
```

Install them:

```bash
uv install -r requirements.txt
```

## Configuration

Before running the server, ensure:

1. DaVinci Resolve Studio is running.
2. Python can access the DaVinci Resolve scripting API (handled automatically by `ResolveAPI` in most cases).

### API Access Configuration

The `ResolveAPI` class dynamically locates the scripting API, but you may need to configure it manually in some cases:

#### macOS

The API is typically available at:

- `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules`
- Or user-specific: `~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules`

No additional setup is usually required.

#### Windows

Add the API path if not detected:

```python
import sys
sys.path.append("C:\\ProgramData\\Blackmagic Design\\DaVinci Resolve\\Support\\Developer\\Scripting\\Modules")
```

#### Linux

Set the environment variable:

```bash
export PYTHONPATH=$PYTHONPATH:/opt/resolve/Developer/Scripting/Modules
```

Alternatively, set a custom path via an environment variable:

```bash
export RESOLVE_SCRIPT_PATH="/custom/path/to/scripting/modules"
```

## Running the Server

Start the MCP server:

```bash
# Run directly with Python
python -m resolve_mcp.server

# Or with uv
uv run resolve_mcp/server.py
```

The server will launch and connect to DaVinci Resolve, logging output like:

```
2025-03-19 ... - resolve_mcp - INFO - Successfully connected to DaVinci Resolve.
```

### Claude Integration Configuration

To integrate with Claude Desktop, update your `claude_desktop_config.json` (e.g., `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "davinci-resolve": {
      "command": "/path/to/uv",
      "args": [
        "run",
        "--directory",
        "/path/to/davinci-resolve-mcp",
        "resolve_mcp/server.py"
      ]
    }
  }
}
```

- Replace `/path/to/uv` with the path to your `uv` executable (e.g., `/usr/local/bin/uv` or `C:\Users\username\.cargo\bin\uv.exe`).
- Replace `/path/to/davinci-resolve-mcp` with the absolute path to your project directory.

Restart Claude Desktop to enable the server. Look for a hammer icon in the input box to confirm integration.

## Troubleshooting

### Connection Issues

If the server fails to connect:

1. Ensure DaVinci Resolve Studio is running.
2. Check Resolve’s preferences to confirm scripting is enabled.
3. Verify Python version compatibility (3.10+ recommended):
   ```bash
   python --version
   ```
4. Confirm API paths are accessible (see logs in `~/Library/Logs/Claude/mcp*.log` on macOS or `%userprofile%\AppData\Roaming\Claude\Logs\` on Windows).

### Dependency Issues

If modules like `mcp` or `pydantic` are missing:

```bash
uv install mcp pydantic
```

### Python Version Compatibility

Switch to a compatible version with `pyenv` if needed:

```bash
pyenv install 3.10.12
pyenv shell 3.10.12
uv install -r requirements.txt
```

## Available Tools and Resources

The MCP server provides extensive functionality through the `ResolveAPI` class:

### Project Management

- Create new projects (`create_project`)
- Load existing projects (`load_project`)
- Save current projects (`save_project`)
- Export/import projects (`export_project`, `import_project`)
- Get/set project settings (`get_project_settings`, `set_project_setting`)

### Timeline Operations

- Create new timelines (`create_timeline`)
- Set/get current timeline (`set_current_timeline`, `get_current_timeline`)
- Add/manage tracks (`add_track`, `set_track_name`, `enable_track`)
- Get timeline items (`get_timeline_items`)
- Set clip properties (`set_clip_property`)
- Add markers (`add_timeline_marker`)

### Media Management

- Import media files (`add_items_to_media_pool`)
- Create media pool folders (`add_sub_folder`)
- Create timelines from clips (`create_timeline_from_clips`)
- Get clip metadata (`get_clip_metadata`)

### Fusion Integration

- Add Fusion compositions to clips (`create_fusion_node`)
- Create/manage Fusion nodes (`create_fusion_node`)
- Access current composition (`get_current_comp`)

### Color Grading

- Get/add color nodes (`get_color_page_nodes`, `add_color_node`)
- Save/apply stills (`save_still`, `apply_still`)
- Manage gallery albums (`get_gallery_albums`)

### Audio Control

- Get/set clip audio volume (`get_audio_volume`, `set_audio_volume`)
- Set track volume (`set_track_volume`)

### Playback Control

- Play/stop playback (`play`, `stop`)
- Get/set playhead position (`get_current_timecode`, `set_playhead_position`)

### Rendering

- Start rendering (`start_render`)
- Get render status (`get_render_status`)

### Navigation

- Open specific pages (`open_page`: Media, Edit, Fusion, Color, Fairlight, Deliver)

### Advanced Operations

- Execute custom Python code (`execute_python`)
- Execute Lua scripts in Fusion (`execute_lua`)

## Development

To contribute:

1. Fork the repository: `https://github.com/yourusername/davinci-resolve-mcp`
2. Create a feature branch: `git checkout -b feature-name`
3. Install dependencies: `uv install -e .`
4. Make changes and test: `uv run resolve_mcp/server.py`
5. Submit a pull request.

## License

[MIT License](LICENSE)

---

### Key Updates

- **Expanded Features**: Added new capabilities like gallery management, track control, audio adjustments, playback, and project export/import to the “Available Tools and Resources” section.
- **Installation Clarity**: Improved `uv` instructions with verification steps and explicit paths for Claude integration.
- **Troubleshooting**: Enhanced with specific commands and log locations for debugging.
- **Configuration**: Updated API access notes to reflect the dynamic path handling in `ResolveAPI`.

This README now fully aligns with the enhanced `ResolveAPI` class, providing a comprehensive guide for users and developers. Let me know if you’d like further adjustments!
