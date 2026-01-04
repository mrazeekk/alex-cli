from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    import tomllib  # py>=3.11
except Exception:  # pragma: no cover
    tomllib = None


@dataclass
class UserConfig:
    language: str = "en"  # cs/en
    model: Optional[str] = None
    # UX
    verbose: bool = False
    auto_yes: bool = False  
    max_output_chars: int = 4000

    # prompt tuning
    style: str = "practical"  # practical/terse/verbose
    safety_level: str = "normal"  # normal/strict

def _config_dir() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else (Path.home() / ".config")
    return base / "alex"

def config_path() -> Path:
    return _config_dir() / "config.toml"

def default_config_text() -> str:
    return """# Alex CLI config (TOML)
# Tip: after editing, just run alex again, the config is always loaded.

language = "en"        # "cs" or "en"
# model = "gpt-4.1-mini"

verbose = false
auto_yes = false
max_output_chars = 4000

style = "practical"    # "practical" | "terse" | "verbose"
safety_level = "normal" # "normal" | "strict"
"""

def ensure_config_file() -> Path:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(default_config_text(), encoding="utf-8")
    return path

def load_config() -> UserConfig:
    path = config_path()
    if not path.exists() or not tomllib:
        return UserConfig()

    raw = path.read_bytes()
    try:
        data = tomllib.loads(raw.decode("utf-8"))
    except Exception:
        # Když je config rozbitý, radši nepadat
        return UserConfig()

    cfg = UserConfig()
    for key in ("language", "model", "verbose", "auto_yes", "max_output_chars", "style", "safety_level"):
        if key in data:
            setattr(cfg, key, data[key])
    return cfg

def open_in_editor(path: Path) -> int:
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL") or "nano"
    try:
        return subprocess.call([editor, str(path)])
    except FileNotFoundError:
        # fallback
        return subprocess.call(["nano", str(path)])
