from __future__ import annotations

import os
import stat
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .render import print_box
from .user_config import config_path
from .auth import get_status, key_path

console = Console()


@dataclass
class Check:
    label: str
    value: str
    status: str  # OK / WARN / FAIL
    hint: Optional[str] = None


def _status_text(s: str) -> Text:
    s = (s or "").upper().strip()
    if s == "OK":
        return Text("OK", style="bold green")
    if s == "WARN":
        return Text("WARN", style="bold yellow")
    return Text("FAIL", style="bold red")


def _file_mode(p: Path) -> str:
    try:
        st = p.stat()
        return oct(stat.S_IMODE(st.st_mode))
    except Exception:
        return "?"


def _overall(checks: List[Check]) -> str:
    statuses = {c.status for c in checks}
    if "FAIL" in statuses:
        return "FAILED"
    if "WARN" in statuses:
        return "WARN"
    return "OK"


def run_doctor() -> int:
    checks: List[Check] = []

    # Python
    py = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} ({sys.executable})"
    checks.append(Check("Python", py, "OK"))

    # alex in PATH
    alex_path = shutil.which("alex") or ""
    if alex_path:
        checks.append(Check("alex in PATH", alex_path, "OK"))
    else:
        checks.append(Check("alex in PATH", "missing", "FAIL", "Reinstall wrapper to /usr/local/bin/alex"))

    # Config file (user config.toml)
    cfg = config_path()
    checks.append(
        Check(
            "Config file",
            f"{cfg} (exists={cfg.exists()})",
            "WARN" if not cfg.exists() else "OK",
            "Run: alex config" if not cfg.exists() else None,
        )
    )

    # OpenAI key status
    st = get_status()
    kf = key_path()
    kf_exists = kf.exists()
    mode = _file_mode(kf) if kf_exists else "?"

    # key file check
    if kf_exists:
        if mode in ("0o600", "0o400"):
            checks.append(Check("Key file", f"{kf} (mode={mode})", "OK"))
        else:
            checks.append(Check("Key file", f"{kf} (mode={mode})", "WARN", "Fix perms: chmod 600 ~/.config/alex/openai.env"))
    else:
        checks.append(Check("Key file", f"{kf} (exists=False)", "WARN", "Run: alex auth"))

    # env var check
    if st.has_env:
        checks.append(Check("OPENAI_API_KEY (env)", "present", "OK", f"Key: {st.masked_key}"))
    else:
        checks.append(Check("OPENAI_API_KEY (env)", "missing", "WARN", "Optional (alex can read from key file)"))

    # final key availability (env OR file)
    if st.has_env or st.has_file:
        checks.append(Check("OpenAI key usable", "yes", "OK", f"Key: {st.masked_key}"))
    else:
        checks.append(Check("OpenAI key usable", "no", "FAIL", "Run: alex auth"))

    # tools
    for tool in ("git", "systemctl", "journalctl"):
        if shutil.which(tool):
            checks.append(Check(tool, "ok", "OK"))
        else:
            checks.append(Check(tool, "missing", "WARN"))

    # shell hook
    hook = Path("/etc/profile.d/alex-shell-hook.sh")
    checks.append(
        Check(
            "Shell hook",
            f"{hook} (exists={hook.exists()})",
            "OK" if hook.exists() else "WARN",
            None if hook.exists() else "Optional: install /etc/profile.d/alex-shell-hook.sh",
        )
    )

    # Render
    t = Table(show_header=True, header_style="bold")
    t.add_column("Check", overflow="fold")
    t.add_column("Status", width=8)
    t.add_column("Value", overflow="fold")
    t.add_column("Hint", overflow="fold")

    for c in checks:
        t.add_row(c.label, _status_text(c.status), c.value, c.hint or "")

    console.print(Panel(t, title="[bold]Alex doctor[/bold]", border_style="white"))

    overall = _overall(checks)
    if overall == "OK":
        print_box(Text("Doctor: OK", style="bold green"), title="Alex")
        return 0
    if overall == "WARN":
        print_box(Text("Doctor: WARN (some optional things missing)", style="bold yellow"), title="Alex")
        return 0

    print_box(Text("Doctor: FAILED. Run: alex auth", style="bold red"), title="Alex")
    return 1
