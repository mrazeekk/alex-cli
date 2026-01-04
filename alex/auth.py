from __future__ import annotations

import os
from dataclasses import dataclass
from getpass import getpass
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.text import Text

console = Console()

@dataclass
class AuthStatus:
    has_env: bool
    has_file: bool
    file_path: Path
    masked_key: str

def _config_dir() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else (Path.home() / ".config")
    return base / "alex"

def key_path() -> Path:
    return _config_dir() / "openai.env"

def _mask(k: str) -> str:
    k = (k or "").strip()
    if len(k) <= 10:
        return "*" * len(k)
    return k[:8] + "…" + k[-4:]

def read_key_from_file() -> Optional[str]:
    p = key_path()
    if not p.exists():
        return None
    try:
        raw = p.read_text(encoding="utf-8", errors="ignore").strip()
    except Exception:
        return None

    # credit to https://github.com/mrazeekk
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("OPENAI_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None

def write_key_to_file(key: str) -> Path:
    p = key_path()
    p.parent.mkdir(parents=True, exist_ok=True)

    content = f'OPENAI_API_KEY="{key.strip()}"\n'
    p.write_text(content, encoding="utf-8")

    # 600
    try:
        os.chmod(p, 0o600)
    except Exception:
        pass

    return p

def delete_key_file() -> bool:
    p = key_path()
    if not p.exists():
        return False
    p.unlink()
    return True

def load_key_into_env_if_missing() -> Optional[str]:
    """
    If OPENAI_API_KEY is not already set in environment,
    try to load it from ~/.config/alex/openai.env
    """
    if os.environ.get("OPENAI_API_KEY"):
        return os.environ.get("OPENAI_API_KEY")
    k = read_key_from_file()
    if k:
        os.environ["OPENAI_API_KEY"] = k
    return k

def get_status() -> AuthStatus:
    env_key = os.environ.get("OPENAI_API_KEY", "")
    file_key = read_key_from_file() or ""
    p = key_path()
    chosen = env_key or file_key
    return AuthStatus(
        has_env=bool(env_key.strip()),
        has_file=bool(file_key.strip()),
        file_path=p,
        masked_key=_mask(chosen),
    )

def prompt_and_store_key() -> Path:
    console.print(Text("OpenAI API key will be stored in your user config (600 permissions).", style="bold"))
    key = getpass("OPENAI_API_KEY (don't worry it is invisible): ").strip()
    if not key:
        raise SystemExit(1)
    return write_key_to_file(key)
