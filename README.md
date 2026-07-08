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

- **DaVinci Resolve _Studio_ 18.0 or newer.** External scripting (which this server
  relies on) is a Studio-only feature. The **free** edition does not expose the
  external scripting API — the server will start but report that it cannot connect.
- **A regular python.org Python 3.10 or 3.11 (64-bit).** Resolve's scripting module
  does `import imp`, which was removed in Python 3.12, so **3.12+ will not work**.
  Do **not** use `uv`-managed Python: its standalone builds crash when loading
  Resolve's native `fusionscript.dll`. See [Setup](#setup-windows) below.
- Access to the DaVinci Resolve scripting API (installed with Resolve).

## Setup (Windows)

> **Why not `uv`?** Two reasons: `uv` defaults to Python 3.13 (fails on `import imp`),
> and even when pinned to 3.10/3.11 its *standalone* Python build crashes when Resolve's
> native `fusionscript.dll` is loaded. Use a normal python.org install with a plain venv.

### 1. Install a compatible Python

Install **python.org Python 3.10 (64-bit)** — for example with winget:

```powershell
winget install --id Python.Python.3.10 -e
```

### 2. Create the virtual environment and install dependencies

From the project directory, create the venv with that interpreter (this repo uses
`.venv310`) and install the dependencies:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe" -m venv .venv310
.\.venv310\Scripts\python.exe -m pip install --upgrade pip
.\.venv310\Scripts\python.exe -m pip install "mcp[cli]>=1.4.1" "pydantic>=2.10.6"
```

### 3. Run the server

Use the provided launcher, which sets up a clean environment for you:

```powershell
.\run_server.ps1
```

`run_server.ps1` builds a minimal `PATH` (exposing only this project's Python 3.10 plus
the Windows system directories) and sets the `RESOLVE_SCRIPT_API` / `RESOLVE_SCRIPT_LIB`
variables. `resolve_env.py` additionally preloads the matching `python3.dll` from inside
the process. Both are needed to avoid the DLL conflict described in
[Troubleshooting](#troubleshooting).

On DaVinci Resolve **Studio** (running), you should see:

```
... - ResolveAPI - INFO - Connected to Resolve using ...
... - resolve_mcp - INFO - Successfully connected to DaVinci Resolve.
```

On the **free** edition it starts but logs (without crashing):

```
... - ResolveAPI - ERROR - DaVinci Resolve scripting could not be initialized.
    External scripting requires DaVinci Resolve Studio; the free edition does not support it.
```

### macOS / Linux

The DLL preload is Windows-specific and is skipped automatically. Ensure a python.org
Python 3.10/3.11, install the same dependencies, and run `python server.py`. The scripting
modules are found automatically; you can override the location with `RESOLVE_SCRIPT_PATH`.

## Claude Desktop Integration

Point Claude Desktop at the launcher via `claude_desktop_config.json`
(`%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "davinci-resolve": {
      "command": "powershell",
      "args": [
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", "C:\\path\\to\\davinci-resolve-mcp\\run_server.ps1"
      ]
    }
  }
}
```

Replace the path with the absolute path to this project. Restart Claude Desktop and look
for the tools/hammer icon to confirm the server loaded.

## Troubleshooting

### "Failed to connect" / "requires DaVinci Resolve Studio"

External scripting is a **Studio-only** feature. On the free edition the scripting library
cannot be initialized from an external process, and the server will run in a disconnected
state. There is no software workaround — Studio is required.

### The process crashes on startup (access violation `0xC0000005`)

Resolve's `fusionscript.dll` loads a Python 3 runtime when the scripting module is
imported. It chooses which one from the `FUSION_PYTHON3_HOME` environment variable and,
**if that is unset, from the Windows registry** (`HKCU`/`HKLM\SOFTWARE\Python\PythonCore`).
On a machine with several Pythons registered — commonly **Anaconda** (`python312.dll`) or a
**python.org 3.13** — that fallback picks a *foreign* runtime, loads it into the 3.10
interpreter, and the process dies with an access violation.

The fix is to set `FUSION_PYTHON3_HOME` to this project's Python 3.10. Both `run_server.ps1`
and `resolve_env.py` do this for you (and additionally preload the correct `python3.dll` and
probe the scripting import in a subprocess so a crash there cannot take down the server), so
**always launch via `run_server.ps1`**. Note that `PATH` isolation alone is *not* enough —
the registry fallback bypasses `PATH` — which is why `FUSION_PYTHON3_HOME` is required.

### It loads but says `scriptapp('Resolve') returned None`

The scripting module imported successfully but no live Resolve object was returned. Either
Resolve isn't running, or external scripting is disabled. In Resolve, open
**Preferences → System → General** and set **"External scripting using"** to **Local**, then
restart Resolve. Remember that external scripting also **requires DaVinci Resolve Studio** —
on the free edition this will remain `None`.

### `import imp` / `ModuleNotFoundError` at startup

You are on Python 3.12 or newer (the `imp` module was removed). Recreate the venv with
Python 3.10 or 3.11 as shown in [Setup](#setup-windows).

### Dependency Issues

If `mcp` or `pydantic` are missing, install them into the venv:

```powershell
.\.venv310\Scripts\python.exe -m pip install "mcp[cli]>=1.4.1" "pydantic>=2.10.6"
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
3. Set up the venv and dependencies (see [Setup](#setup-windows)).
4. Make changes and test: `.\run_server.ps1`
5. Submit a pull request.

## License

[MIT License](LICENSE)
