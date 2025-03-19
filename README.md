# DaVinci Resolve MCP Server

A Model Context Protocol (MCP) server that enables AI assistants like Claude to interact with DaVinci Resolve Studio.

## Overview

This server implements the MCP protocol to create a bridge between AI assistants and DaVinci Resolve. It allows AI assistants to:

- Create and manage DaVinci Resolve projects
- Create and manipulate timelines
- Import media files
- Access the Fusion composition system
- Navigate between different pages in DaVinci Resolve
- Execute custom Python and Lua scripts

## Requirements

- DaVinci Resolve Studio 18.0 or newer
- Python 3.10 or newer
- Access to the DaVinci Resolve scripting API

## Installation with uv

[uv](https://github.com/astral-sh/uv) is a modern Python package installer and resolver that's faster than pip. Here's how to install and set up the DaVinci Resolve MCP server using uv:

### 1. Install uv

If you don't have uv installed already:

```bash
# Using pip
pip install uv

# Using Homebrew (macOS)
brew install uv

# Using Conda
conda install -c conda-forge uv
```

### 2. Create a virtual environment

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install the DaVinci Resolve MCP server

```bash
# From the project directory
uv install -e .

# Or directly from a specific branch on GitHub
uv install git+https://github.com/yourusername/davinci-resolve-mcp.git
```

### 4. Install dependencies

```bash
uv install -r requirements.txt
```

## Configuration

Before running the server, ensure that:

1. DaVinci Resolve is running
2. Python can access the DaVinci Resolve scripting API

### API Access Configuration

#### macOS

On macOS, the Python scripting API should automatically be available if DaVinci Resolve is installed.

#### Windows

On Windows, you might need to add the DaVinci Resolve API path to your Python path:

```python
import sys
sys.path.append("C:\\Program Files\\Blackmagic Design\\DaVinci Resolve\\fusionscript.dll")
```

#### Linux

On Linux, add the following to your environment:

```bash
export PYTHONPATH=$PYTHONPATH:/opt/resolve/Developer/Scripting
```

## Running the Server

To start the MCP server:

```bash
# Run the server directly
python -m resolve_mcp.server

# Or if installed via uv
mcp run resolve_mcp.server
```

The server will start and listen for connections from AI assistants. You should see output indicating that it has successfully connected to DaVinci Resolve.

### Claude Integration Configuration

To use the server with Claude, add the following configuration to your Claude tools JSON configuration:

```json
{
  "davinci-resolve": {
    "command": "uv",
    "args": ["--directory", "/path_to/davinci-resolve-mcp", "run", "server.py"]
  }
}
```

Make sure to update the directory path to match the location of your DaVinci Resolve MCP installation.

## Troubleshooting

### Connection Issues

If the server cannot connect to DaVinci Resolve:

1. Ensure DaVinci Resolve is running
2. Verify that scripting is enabled in DaVinci Resolve preferences
3. Check that your Python version matches the version supported by DaVinci Resolve (Python 3.10+ recommended)
4. Ensure the API paths are correctly set up for your operating system

### Python Version Compatibility

This server requires Python 3.10 or newer. If you're using pyenv to manage Python versions:

```bash
pyenv shell 3.10.12  # Or your specific 3.10+ version
python --version     # Verify the version
uv install -r requirements.txt
```

## Available Tools and Resources

The MCP server provides the following functionality:

### Project Management

- Create new projects
- Load existing projects
- Save current projects

### Timeline Operations

- Create new timelines
- Set the current timeline
- Get timeline information

### Media Management

- Import media files
- Create media pool folders
- Create timelines from clips

### Fusion Integration

- Add Fusion compositions to clips
- Create Fusion nodes
- Create chains of connected Fusion nodes

### Navigation

- Open specific pages in DaVinci Resolve (Media, Edit, Fusion, Color, Fairlight, Deliver)

### Advanced Operations

- Execute custom Python code
- Execute Lua scripts in Fusion

## Development

To contribute to the development:

1. Fork the repository
2. Create a new branch for your feature
3. Make your changes
4. Submit a pull request

## License

[MIT License](LICENSE)
