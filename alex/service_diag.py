from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from rich.prompt import Confirm
from rich.table import Table
from rich.text import Text

from .render import print_box, render_structured
from .openai_client import call_responses_structured
from .executor import run_command, clean_stderr, classify_blacklist
from .utils import ensure_key


@dataclass
class CmdResult:
    cmd: str
    returncode: int
    stdout: str
    stderr: str


def _format_results(results: List[CmdResult]) -> str:
    chunks = []
    for r in results:
        out = (r.stdout or "").strip()
        err = (r.stderr or "").strip()
        chunks.append(
            f"### CMD\n{r.cmd}\n"
            f"### EXIT\n{r.returncode}\n"
            f"### STDOUT\n{out[:8000]}\n"
            f"### STDERR\n{err[:8000]}\n"
        )
    return "\n\n".join(chunks)


def _run_diag(cmds: List[str]) -> List[CmdResult]:
    res: List[CmdResult] = []
    for c in cmds:
        p = run_command(c)
        res.append(
            CmdResult(
                cmd=c,
                returncode=p.returncode,
                stdout=(p.stdout or ""),
                stderr=clean_stderr(p.stderr or ""),
            )
        )
    return res


def service_diagnose(
    service: str,
    apply: bool = False,
    yes: bool = False,
    max_rounds: int = 3,
) -> None:
    """
    Multi-step systemd service diagnostic:
    - baseline systemctl + journalctl
    - ask model what to run next
    - run suggested read-only probes (optionally ask)
    """

    ensure_key()

    # 0) baseline probes (safe)
    base_cmds = [
        f"systemctl status {service} --no-pager --full",
        f"systemctl is-enabled {service}",
        f"systemctl is-active {service}",
        # show where the unit file is, and key metadata
        f"systemctl show {service} -p Id -p Names -p LoadState -p ActiveState -p SubState -p Result -p ExecMainStatus -p ExecMainCode -p FragmentPath -p DropInPaths -p MainPID",
        # last logs (current boot). if service doesn't exist, this is still useful.
        f"journalctl -u {service} -b --no-pager -n 200",
    ]

    results = _run_diag(base_cmds)
    baseline_text = _format_results(results)

    # 1) iterative loop: model asks for more probes
    context = (
        "You are diagnosing a systemd service on Debian.\n"
        "Goal: Determine if the service exists and whether it is healthy.\n"
        "If failing: determine the most likely root cause (config error, missing file, permissions, port in use, etc.)\n"
        "When you need more evidence, propose additional SAFE diagnostic commands.\n"
        "Prefer read-only commands.\n"
        "If you suspect a port conflict, ask to run ss/lsof and identify the owning process.\n"
        "If you suspect a bad config, ask to show the relevant config file location and show the exact problematic lines.\n"
        "Return JSON matching schema (intent=general is ok).\n"
    )

    prompt = (
        f"SERVICE: {service}\n\n"
        f"BASELINE RESULTS:\n{baseline_text}\n\n"
        "Request: Diagnose this service. If you need more info, return commands[] to run.\n"
        "Important: commands should be SAFE diagnostics (no edits). If you recommend changes, put them in notes.\n"
    )

    for round_i in range(1, max_rounds + 1):
        data = call_responses_structured(context + "\n\n" + prompt, intent="general")
        render_structured(data)

        cmds = data.get("commands", [])
        if not cmds:
            # model is done
            return

        # run suggested diagnostic commands
        total = len(cmds)
        for idx, c in enumerate(cmds, start=1):
            cmd = (c.get("cmd") or "").strip()
            if not cmd:
                continue

            # force to SUPER_HIGH if blacklist hits (even though we asked for safe)
            bl = classify_blacklist(cmd)
            risk = c.get("risk", "low")
            if bl:
                risk = "super_high"

            if not apply:
                # if user didn't ask to apply, we only show plan
                continue

            if risk == "super_high":
                msg = f"[round {round_i}] Run SUPER_HIGH diagnostic?\n{cmd}\nReason: {bl or 'blacklist match'}"
                if not Confirm.ask(msg, default=False):
                    continue
            else:
                if not yes:
                    if not Confirm.ask(f"[round {round_i}] Run diagnostic?\n{cmd}", default=True):
                        continue

            r = run_command(cmd)
            results.append(
                CmdResult(
                    cmd=cmd,
                    returncode=r.returncode,
                    stdout=(r.stdout or ""),
                    stderr=clean_stderr(r.stderr or ""),
                )
            )

        if not apply:
            # user just wanted the analysis plan, not execution
            return

        # feed back the new results and loop
        prompt = (
            f"SERVICE: {service}\n\n"
            f"ALL RESULTS SO FAR:\n{_format_results(results)}\n\n"
            "Continue diagnosis. If done, return commands=[] and put final answer in summary/notes.\n"
        )

    # if we hit max rounds
    print_box("Reached max diagnostic rounds. If you want, run again with more rounds.", title="Alex")
