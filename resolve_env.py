"""
Environment bootstrap for connecting to DaVinci Resolve's scripting API.

Why this module exists
----------------------
Resolve's ``fusionscript`` native library exports its Python entry points against
the version-agnostic ``python3.dll`` forwarder (Windows). If *another* Python's
``python3.dll`` is found on the DLL search path first -- e.g. an Anaconda 3.12 or
a python.org 3.13 install -- that foreign runtime gets loaded into this
interpreter and the process dies with an access violation (0xC0000005) the moment
``DaVinciResolveScript`` imports the library.

Preloading *this* interpreter's own ``python3.dll`` makes ``fusionscript`` bind to
the correct runtime. We also register the scripting module + library locations via
the ``RESOLVE_SCRIPT_*`` variables that Blackmagic's ``DaVinciResolveScript.py``
looks for.

Importing this module runs the bootstrap automatically. Import it *before*
anything that pulls in ``DaVinciResolveScript`` / ``resolve_api``.
"""

import os
import subprocess
import sys

# Cache for the one-time "is it safe to import the scripting module?" probe.
_safe_to_import = None


def _resolve_program_dir() -> str:
    """Directory of the Resolve application (holds fusionscript.dll on Windows)."""
    if sys.platform == "win32":
        return os.path.join(
            os.environ.get("PROGRAMFILES", r"C:\Program Files"),
            "Blackmagic Design", "DaVinci Resolve",
        )
    if sys.platform == "darwin":
        return "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion"
    return "/opt/resolve/libs/Fusion"


def _scripting_dir() -> str:
    """Root of the Developer/Scripting package that ships the import modules."""
    if sys.platform == "win32":
        return os.path.join(
            os.environ.get("PROGRAMDATA", r"C:\ProgramData"),
            "Blackmagic Design", "DaVinci Resolve",
            "Support", "Developer", "Scripting",
        )
    if sys.platform == "darwin":
        return "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
    return "/opt/resolve/Developer/Scripting"


def _script_lib() -> str:
    """Absolute path to the fusionscript native library for this platform."""
    if sys.platform == "win32":
        return os.path.join(_resolve_program_dir(), "fusionscript.dll")
    if sys.platform == "darwin":
        return os.path.join(_resolve_program_dir(), "fusionscript.so")
    return os.path.join(_resolve_program_dir(), "fusionscript.so")


def _set_env_defaults() -> None:
    """Point DaVinciResolveScript.py at the API/library and add Modules to sys.path."""
    api = _scripting_dir()
    modules = os.path.join(api, "Modules")
    os.environ.setdefault("RESOLVE_SCRIPT_API", api)
    os.environ.setdefault("RESOLVE_SCRIPT_LIB", _script_lib())
    # Propagate the Modules dir to child processes via PYTHONPATH (used by the
    # safety probe below). We deliberately do NOT touch this process's sys.path --
    # resolve_api._find_scripting_module() adds it itself and only returns a path
    # when it is not already present, so pre-inserting it would break detection.
    existing = os.environ.get("PYTHONPATH", "")
    if modules not in existing.split(os.pathsep):
        os.environ["PYTHONPATH"] = os.pathsep.join(p for p in (modules, existing) if p)


def _preload_matching_python_dll() -> None:
    """
    Force Resolve's fusionscript to bind to THIS interpreter's runtime by loading
    our own ``python3.dll`` first. No-op off Windows, where the .so is resolved by
    absolute path and there is no forwarder ambiguity.
    """
    if sys.platform != "win32":
        return
    import ctypes

    py3 = os.path.join(sys.base_prefix, "python3.dll")
    if os.path.exists(py3):
        try:
            ctypes.WinDLL(py3)
        except OSError:
            pass
    # Prefer our interpreter dir and the Resolve program dir for DLL resolution.
    for d in (sys.base_prefix, _resolve_program_dir()):
        if d and os.path.isdir(d):
            try:
                os.add_dll_directory(d)
            except OSError:
                pass


def scripting_safe_to_import() -> bool:
    """
    Return True if importing ``DaVinciResolveScript`` in *this* process is safe.

    Loading fusionscript can hard-crash the interpreter (uncatchable access
    violation) on setups where external scripting is unavailable -- most notably
    the free edition of DaVinci Resolve, which gates external scripting to Studio.
    We can't catch a native crash, so we reproduce the import in a throwaway
    subprocess and treat a crash there as "not safe".

    Exit-code contract of the probe:
        0  -> imported and scriptapp() returned a live object (connected)
        10 -> imported cleanly but scriptapp() returned None (Studio, app closed)
        anything else / no exit -> the import crashed; do not attempt in-process
    """
    global _safe_to_import
    if _safe_to_import is not None:
        return _safe_to_import

    probe = (
        "import resolve_env, sys\n"
        "import DaVinciResolveScript as d\n"
        "sys.exit(0 if d.scriptapp('Resolve') else 10)\n"
    )
    env = os.environ.copy()
    # Ensure the child can import this module (resolve_env) and the Modules dir.
    here = os.path.dirname(os.path.abspath(__file__))
    env["PYTHONPATH"] = os.pathsep.join(
        p for p in (here, env.get("PYTHONPATH", "")) if p
    )
    try:
        result = subprocess.run(
            [sys.executable, "-c", probe],
            cwd=here,
            env=env,
            capture_output=True,
            timeout=60,
        )
        _safe_to_import = result.returncode in (0, 10)
    except (subprocess.TimeoutExpired, OSError):
        _safe_to_import = False
    return _safe_to_import


# Run the bootstrap on import.
_preload_matching_python_dll()
_set_env_defaults()
