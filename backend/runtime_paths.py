"""Runtime paths for source and frozen (PyInstaller) executions."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def bundled_root() -> Path:
    """Return the read-only root containing PyInstaller bundled resources."""
    return Path(getattr(sys, "_MEIPASS", PROJECT_ROOT))


def data_dir() -> Path:
    """Return the writable per-user directory used by a packaged app."""
    override = os.getenv("INVESTMENT_ASSISTANT_DATA_DIR")
    if override:
        path = Path(override).expanduser()
    elif not is_frozen():
        path = PROJECT_ROOT
    elif sys.platform == "win32":
        path = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData/Local")) / "InvestmentAssistant"
    elif sys.platform == "darwin":
        path = Path.home() / "Library/Application Support/InvestmentAssistant"
    else:
        path = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local/share")) / "InvestmentAssistant"

    path.mkdir(parents=True, exist_ok=True)
    return path


def env_file() -> Path:
    """Return the settings file: project .env in dev, user data in packages."""
    override = os.getenv("INVESTMENT_ASSISTANT_ENV_FILE")
    if override:
        path = Path(override).expanduser()
    elif is_frozen():
        path = data_dir() / ".env"
    else:
        # Development must always use the repository root .env, regardless of
        # the shell's current working directory.
        path = PROJECT_ROOT / ".env"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def runtime_file(name: str) -> Path:
    path = data_dir() / name
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def mcp_config_file() -> Path:
    """Return a writable MCP config, seeded from the bundled default."""
    override = os.getenv("INVESTMENT_ASSISTANT_MCP_CONFIG")
    if override:
        return Path(override).expanduser()

    path = runtime_file("mcp_config.yaml")
    if not path.exists():
        bundled = bundled_root() / "mcp_config.yaml"
        if not bundled.exists():
            bundled = bundled_root() / "backend" / "mcp_config.yaml"
        if not bundled.exists():
            bundled = PROJECT_ROOT / "backend" / "mcp_config.yaml"
        if bundled.exists():
            shutil.copyfile(bundled, path)
    return path


def resolve_runtime_path(value: str) -> str:
    """Resolve relative user paths inside the writable packaged data directory."""
    path = Path(value).expanduser()
    if path.is_absolute():
        return str(path)
    base = data_dir() if is_frozen() else PROJECT_ROOT
    return str(base / path)
