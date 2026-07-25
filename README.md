# DaVinci Resolve MCP Server

Control DaVinci Resolve Studio from MCP clients such as Claude Desktop.

This project exposes Resolve projects, timelines, media, Fusion, color, audio,
playback, and rendering operations through a local
[Model Context Protocol](https://modelcontextprotocol.io/) server.

## What it does

The server provides:

- 32 MCP tools for editing and controlling Resolve;
- 6 read-only MCP resources describing the current Resolve state;
- automatic discovery of the DaVinci Resolve scripting API on Windows, macOS,
  and Linux;
- a protected native-module probe, so a broken `fusionscript` import does not
  crash the MCP server;
- Windows runtime isolation to prevent Resolve from loading an incompatible
  Python DLL.

Example requests from an MCP client:

> Create a project called “Product Launch”.

> Import these three clips and create a timeline called “Rough Cut”.

> Add a blue marker at frame 240 with the note “Review transition”.

> Save the current grade as a still in the “Approved Looks” album.

## Requirements

- **DaVinci Resolve Studio 18 or newer.** External scripting must be enabled.
- **64-bit CPython 3.10 or 3.11.** Resolve's scripting module still imports
  `imp`, which was removed from Python 3.12.
- The DaVinci Resolve scripting API installed with Resolve.
- An MCP client such as Claude Desktop.

Before starting the server, open Resolve and set:

**Preferences → System → General → External scripting using → Local**

The free edition of Resolve does not expose the external scripting connection
used by this server. The MCP process can start, but it will remain disconnected.

## Installation

Clone the repository first:

```bash
git clone https://github.com/Tooflex/davinci-resolve-mcp.git
cd davinci-resolve-mcp
```

### Windows

Use a regular 64-bit Python from python.org. Do not use a `uv`-managed standalone
Python on Windows: Resolve's `fusionscript.dll` is known to crash with those
builds.

Install Python 3.10:

```powershell
winget install --id Python.Python.3.10 -e
```

Create the environment and install the dependencies:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe" -m venv .venv310
.\.venv310\Scripts\python.exe -m pip install --upgrade pip
.\.venv310\Scripts\python.exe -m pip install "mcp[cli]>=1.4.1" "pydantic>=2.10.6"
```

Start the server through the Windows launcher:

```powershell
.\run_server.ps1
```

Always use `run_server.ps1` on Windows. It pins Resolve to the correct Python
runtime, isolates `PATH`, and configures the scripting API paths before starting
the server.

### macOS

Create a virtual environment with CPython 3.10 or 3.11:

```bash
python3.11 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install "mcp[cli]>=1.4.1" "pydantic>=2.10.6"
```

Start the server:

```bash
./.venv/bin/python server.py
```

The standard Resolve API locations are detected automatically:

- `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules`
- `~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules`

Both Intel and Apple Silicon Macs use the same Resolve application and scripting
paths.

### Linux

Create the environment and install the dependencies:

```bash
python3.11 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install "mcp[cli]>=1.4.1" "pydantic>=2.10.6"
./.venv/bin/python server.py
```

The default Linux scripting path is `/opt/resolve/Developer/Scripting/Modules`.

## MCP client configuration

The server uses the MCP standard I/O transport. Configure your client to launch
the server as a local process.

### Claude Desktop on Windows

Edit `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "davinci-resolve": {
      "command": "powershell",
      "args": [
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "C:\\absolute\\path\\to\\davinci-resolve-mcp\\run_server.ps1"
      ]
    }
  }
}
```

### Claude Desktop on macOS

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "davinci-resolve": {
      "command": "/absolute/path/to/davinci-resolve-mcp/.venv/bin/python",
      "args": [
        "/absolute/path/to/davinci-resolve-mcp/server.py"
      ]
    }
  }
}
```

### Other MCP clients

Use the same command and argument pairs shown above:

- Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File <run_server.ps1>`
- macOS/Linux: `<venv-python> <server.py>`

Use absolute paths. Keep Resolve running, restart the MCP client after changing
its configuration, and then check that the `davinci-resolve` tools are available.

## Available MCP resources

| URI | Description |
| --- | --- |
| `system://status` | Connection, project, and timeline status |
| `project://current` | Current project name and timeline count |
| `timeline://current` | Current timeline name, duration, and video-track count |
| `timeline://items` | Items on the first video track |
| `mediapool://current` | Current media-pool folder and clip count |
| `gallery://albums` | Gallery album names |

## Available MCP tools

### Projects and navigation

| Tool | Operation |
| --- | --- |
| `refresh` | Refresh cached Resolve objects |
| `create_project` | Create a project |
| `load_project` | Open an existing project |
| `save_project` | Save the current project |
| `export_project` | Export a project to a file |
| `import_project` | Import a project file |
| `set_project_setting` | Change a project setting |
| `open_page` | Open Media, Edit, Fusion, Color, Fairlight, or Deliver |

### Media and timelines

| Tool | Operation |
| --- | --- |
| `import_media` | Import files into the media pool |
| `add_sub_folder` | Add a media-pool subfolder |
| `create_timeline` | Create an empty timeline |
| `set_current_timeline` | Select a timeline by its 1-based index |
| `append_to_timeline` | Append named clips |
| `create_timeline_from_clips` | Build a timeline from named clips |
| `import_timeline_from_file` | Import a timeline such as XML or EDL |
| `set_clip_property` | Change a timeline clip property |
| `add_timeline_marker` | Add a marker at a frame |
| `add_track` | Add a video, audio, or subtitle track |
| `set_track_name` | Rename a track |
| `enable_track` | Enable or disable a track |
| `set_current_version` | Select a color or Fusion clip version |

### Fusion and color

| Tool | Operation |
| --- | --- |
| `execute_lua` | Execute Lua in Resolve's Fusion environment |
| `create_fusion_node` | Add a node to the current Fusion composition |
| `add_color_node` | Add a color node to the current clip |
| `save_still` | Save the current grade to a gallery album |
| `apply_still` | Apply a named still to a clip |

`execute_lua` runs code inside Resolve. Only execute scripts from sources you
trust.

### Audio, playback, and rendering

| Tool | Operation |
| --- | --- |
| `set_audio_volume` | Set a named clip's audio volume |
| `set_track_volume` | Set an audio-track volume |
| `play_timeline` | Start playback |
| `stop_timeline` | Stop playback |
| `set_playhead_position` | Move the playhead to a frame |
| `start_project_render` | Start a render with an optional preset and output path |

## How the connection bootstrap works

`server.py` imports `resolve_env.py` before creating `ResolveAPI`.

On every platform, the bootstrap:

1. selects the Resolve scripting API and native library paths;
2. propagates the selected Modules directory to child processes;
3. probes `DaVinciResolveScript` in a disposable subprocess;
4. imports the native library in the MCP process only when the probe exits
   safely.

On Windows, Resolve may otherwise select a Python runtime from the Windows
registry and load a foreign `python3xx.dll` into the current process.
`FUSION_PYTHON3_HOME`, DLL preloading, and the isolated launcher prevent that
native crash.

## Environment overrides

Defaults work for standard Resolve installations. For a custom installation,
set these variables before starting the server:

| Variable | Purpose |
| --- | --- |
| `RESOLVE_SCRIPT_PATH` | Directory containing `DaVinciResolveScript.py` |
| `RESOLVE_SCRIPT_API` | Root of Resolve's `Developer/Scripting` directory |
| `RESOLVE_SCRIPT_LIB` | Absolute path to `fusionscript.dll` or `fusionscript.so` |
| `FUSION_PYTHON3_HOME` | Windows Python runtime Resolve must load |

Example:

```bash
export RESOLVE_SCRIPT_PATH="/custom/Developer/Scripting/Modules"
export RESOLVE_SCRIPT_API="/custom/Developer/Scripting"
export RESOLVE_SCRIPT_LIB="/custom/Fusion/fusionscript.so"
./.venv/bin/python server.py
```

## Troubleshooting

### The server starts but is not connected

- Confirm that DaVinci Resolve Studio is running.
- Set **External scripting using** to **Local**, then restart Resolve.
- Confirm that the configured Python is version 3.10 or 3.11.
- Check that the Resolve scripting Modules directory exists.

The server intentionally remains available in a disconnected state when it
cannot initialize Resolve.

### `scriptapp('Resolve') returned None`

The native module loaded, but it could not obtain a running Resolve object.
Resolve is either closed, external scripting is disabled, or the installed
edition does not support external scripting.

### `ModuleNotFoundError: No module named 'imp'`

Python 3.12 or newer is being used. Recreate the virtual environment with Python
3.10 or 3.11.

### Windows access violation `0xC0000005`

Launch the project through `run_server.ps1`, not with `python server.py`.

The crash occurs when `fusionscript.dll` loads an incompatible Python runtime,
often from another python.org or Anaconda installation registered on the
machine. The launcher sets `FUSION_PYTHON3_HOME` and isolates DLL resolution.

### `No valid Resolve scripting module path found`

Set `RESOLVE_SCRIPT_PATH` to the directory containing
`DaVinciResolveScript.py`. If the native library is also in a non-standard
location, set `RESOLVE_SCRIPT_LIB`.

### Missing MCP dependencies

Install the dependencies into the same interpreter configured in the MCP client:

```bash
python -m pip install "mcp[cli]>=1.4.1" "pydantic>=2.10.6"
```

## Development

Run the unit tests:

```bash
python -m unittest discover -s tests -v
```

Run syntax checks:

```bash
python -m py_compile server.py resolve_api.py resolve_env.py
```

The GitHub Actions workflow runs the unit tests on Python 3.10 and 3.11 across
Windows, macOS, and Linux.

Contributions should keep platform-specific bootstrap behavior covered by tests.
