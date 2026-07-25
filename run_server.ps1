<#
    Launches the DaVinci Resolve MCP server with a clean, isolated environment.

    Why a launcher: Resolve's fusionscript library loads a Python 3 runtime when
    the scripting module is imported. It picks that runtime from
    FUSION_PYTHON3_HOME (set below) and, if unset, from the Windows registry --
    where another install (Anaconda 3.12, python.org 3.13, ...) can win and get
    loaded into this 3.10 interpreter, crashing it. We pin FUSION_PYTHON3_HOME to
    this project's Python 3.10, build a minimal PATH that exposes only it plus the
    Windows system dirs, and `resolve_env.py` also sets the var + preloads the
    correct python3.dll from inside the process as defense in depth.

    NOTE: Connecting to Resolve requires DaVinci Resolve *Studio*. The free edition
    does not expose external scripting and the server will report that it could not
    connect (it will not crash -- resolve_env probes safely first).
#>

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

$venvPy = Join-Path $root ".venv310\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    throw "Virtual environment not found at $venvPy. See README for setup."
}

# Resolve the base Python 3.10 install (the venv's 'home') from pyvenv.cfg.
$pyBase = (Get-Content (Join-Path $root ".venv310\pyvenv.cfg") |
    Where-Object { $_ -match '^\s*home\s*=' } |
    ForEach-Object { ($_ -split '=', 2)[1].Trim() } |
    Select-Object -First 1)

# Minimal PATH: only our 3.10 + Windows system dirs. Deliberately excludes any
# other Python / Anaconda dirs that would hijack the fusionscript DLL binding.
$env:PATH = @(
    (Join-Path $root ".venv310\Scripts"),
    $pyBase,
    (Join-Path $env:SystemRoot "System32"),
    $env:SystemRoot
) -join ';'

$scripting = Join-Path $env:PROGRAMDATA "Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting"
$env:RESOLVE_SCRIPT_API = $scripting
$env:RESOLVE_SCRIPT_LIB = Join-Path $env:PROGRAMFILES "Blackmagic Design\DaVinci Resolve\fusionscript.dll"
$env:PYTHONPATH = Join-Path $scripting "Modules"

# Pin the Python that Resolve's fusionscript binds to. Without this it consults
# the registry and may load a foreign interpreter (e.g. Anaconda's python312.dll)
# into this 3.10 process, crashing it with an access violation. See resolve_env.py.
$env:FUSION_PYTHON3_HOME = $pyBase

& $venvPy (Join-Path $root "server.py")
