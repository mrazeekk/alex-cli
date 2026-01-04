import os, shlex, subprocess, re
from typing import Optional

APT_WARNING_RE = re.compile(r"^WARNING: apt does not have a stable CLI interface\.", re.IGNORECASE)

BLACKLIST_PATTERNS = [
    (re.compile(r"\brm\s+-rf\b", re.IGNORECASE), "rm -rf is destructive"),
    (re.compile(r"\bmkfs(\.|$)", re.IGNORECASE), "mkfs formats filesystems"),
    (re.compile(r"\bdd\b.*\bif=", re.IGNORECASE), "dd can overwrite disks"),
    (re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", re.IGNORECASE), "fork bomb"),
    (re.compile(r"\bshutdown\b|\breboot\b|\bpoweroff\b", re.IGNORECASE), "system power control"),
    (re.compile(r"\b(chmod|chown)\b\s+-R\s+/\b", re.IGNORECASE), "recursive permission change on /"),
    (re.compile(r"(?:^|\s)>(?:>?)\s*/etc/", re.IGNORECASE), "redirect into /etc"),
    (re.compile(r"\btee\b.*\s/etc/", re.IGNORECASE), "writing into /etc"),
    (re.compile(r"\bcurl\b.*\|\s*(bash|sh)\b", re.IGNORECASE), "pipe to shell"),
    (re.compile(r"\bwget\b.*\|\s*(bash|sh)\b", re.IGNORECASE), "pipe to shell"),
]

def classify_blacklist(cmd: str) -> Optional[str]:
    for rx, reason in BLACKLIST_PATTERNS:
        if rx.search(cmd):
            return reason
    return None

def clean_stderr(stderr: str) -> str:
    lines = []
    for line in (stderr or "").splitlines():
        if APT_WARNING_RE.match(line.strip()):
            continue
        lines.append(line)
    return "\n".join(lines).strip()

def normalize_command(cmd: str) -> str:
    c = cmd.strip()
    if c.startswith("systemctl status ") and "--no-pager" not in c:
        c += " --no-pager --full"
    if c.startswith("journalctl ") and "--no-pager" not in c:
        c += " --no-pager"
    return c

def run_command(cmd: str) -> subprocess.CompletedProcess:
    shell_ops = ["|", "&&", "||", ";", ">", "<", "$(", "`"]
    cmd = normalize_command(cmd)

    env = os.environ.copy()
    env["SYSTEMD_PAGER"] = "cat"
    env["SYSTEMD_LESS"] = "FRSXMK"

    try:
        if any(op in cmd for op in shell_ops):
            return subprocess.run(["bash", "-lc", cmd], text=True, capture_output=True, env=env)
        args = shlex.split(cmd)
        return subprocess.run(args, text=True, capture_output=True, env=env)

    except FileNotFoundError:
        missing = shlex.split(cmd)[0] if cmd.strip() else cmd
        return subprocess.CompletedProcess(args=cmd, returncode=127, stdout="", stderr=f"bash: {missing}: command not found\n")
    except Exception as e:
        return subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr=f"alex: failed to run command: {e}\n")
