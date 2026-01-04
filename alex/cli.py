import sys
import typer
from typing import List, Optional
from rich.prompt import Confirm
from rich.console import Console
from rich.table import Table
from rich.text import Text

from .render import print_box, render_structured
from .openai_client import call_responses_structured
from .errors import read_error_log_blocks, filter_error_blocks
from .executor import run_command, classify_blacklist, clean_stderr
from .config import ALEX_ERR_FILE_DEFAULT
from .utils import ensure_key
from .user_config import ensure_config_file, open_in_editor, config_path, load_config
from .service_diag import service_diagnose


console = Console()
app = typer.Typer(add_completion=False)

@app.command()
def run(
    query: List[str],
    apply: bool = typer.Option(False, "--apply", help="Execute suggested commands"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Auto-confirm low/medium/high (still asks for super_high/blacklist)"),
    verbose: bool = typer.Option(False, "--verbose", help="Show full stdout/stderr even on success"),
):
    ensure_key()
    cfg = load_config()
    if not verbose and cfg.verbose:
        verbose = True
    if not yes and cfg.auto_yes:
        yes = True

    q = " ".join(query).strip()
    if not q:
        raise SystemExit(1)

    data = call_responses_structured(q, intent="general")
    render_structured(data)

    if not apply:
        return

    cmds = data.get("commands", [])
    total = len(cmds)
    if total == 0:
        print_box("No commands to run.", title="Alex")
        return

    console.print()
    console.print(f"[bold]Execution[/bold]  ({total} commands)")
    console.print()

    for i, c in enumerate(cmds, start=1):
        cmd = (c.get("cmd") or "").strip()
        risk = c.get("risk", "low")

        if not cmd:
            print_box(f"[{i}/{total}] ⏭ Skipped\nEmpty command.", title="Alex")
            continue

        bl_reason = classify_blacklist(cmd)
        if bl_reason:
            risk = "super_high"

        if risk == "super_high":
            msg = f"[{i}/{total}] Run SUPER_HIGH risk command?\n{cmd}"
            if bl_reason:
                msg += f"\nReason: {bl_reason}"
            if not Confirm.ask(msg, default=False):
                print_box(f"[{i}/{total}] ⏭ Skipped\n{cmd}", title="Alex")
                continue
        else:
            if not yes:
                if not Confirm.ask(f"[{i}/{total}] Run command?\n{cmd}", default=True):
                    print_box(f"[{i}/{total}] ⏭ Skipped\n{cmd}", title="Alex")
                    continue

        result = run_command(cmd)
        out = (result.stdout or "").strip()
        err = clean_stderr(result.stderr or "")

        ok = (result.returncode == 0)
        status = "✅ SUCCESS" if ok else "❌ FAILED"
        status_style = "green" if ok else "bold red"

        body = Table.grid(padding=(0, 1))
        body.add_row(Text(f"[{i}/{total}] {status}", style=status_style))
        body.add_row(Text(cmd, style="bold"))
        body.add_row(Text(f"Exit code: {result.returncode}"))

        always_show_stdout = False
        always_show_stderr = False

        status_like_prefixes = (
            "systemctl status ",
            "systemctl is-active ",
            "systemctl is-enabled ",
            "systemctl list-units",
            "systemctl list-unit-files",
            "journalctl ",
            "ss ",
            "ip ",
            "ufw status",
            "firewall-cmd ",
            "docker ps",
            "podman ps",
        )

        cmd_l = cmd.lower().strip()

        if any(cmd_l.startswith(p) for p in status_like_prefixes):
            always_show_stdout = True

        if ("--version" in cmd_l) or cmd_l.endswith(" -v") or cmd_l.endswith(" -version") or (" version" in cmd_l):
            always_show_stdout = True
            always_show_stderr = True

        show_stdout = (not ok) or verbose or always_show_stdout
        show_stderr = (not ok) or verbose or always_show_stderr or bool(err)

        if ok and out:
            show_stdout = True

        if ok and err and always_show_stderr:
            show_stderr = True


        if show_stdout and out:
            body.add_row(Text(""))
            body.add_row(Text("STDOUT", style="bold"))
            limit = cfg.max_output_chars if cfg.max_output_chars else 4000
            body.add_row(Text(out[-limit:]))

        if show_stderr and err:
            body.add_row(Text(""))
            body.add_row(Text("STDERR", style="bold red" if not ok else "bold yellow"))
            limit = cfg.max_output_chars if cfg.max_output_chars else 4000
            body.add_row(Text(err[-limit:]))


        print_box(body, title="Alex")


@app.command()
def error(
    text: List[str] = typer.Argument(None),
    cmd: Optional[str] = typer.Option(None, "--cmd", help="Original command you ran"),
    fallback: str = typer.Option(ALEX_ERR_FILE_DEFAULT, "--fallback", help="Fallback error file"),
    last: int = typer.Option(1, "--last", "-n", help="How many last errors to include"),
    show: bool = typer.Option(False, "--show", help="Only show the selected error block(s) without analysis"),
    grep: Optional[str] = typer.Option(None, "--grep", help="Filter errors containing this text (case-insensitive)"),
    since: Optional[str] = typer.Option(None, "--since", help="Only errors since date/time (YYYY-MM-DD or YYYY-MM-DD HH:MM[:SS])"),
    clear: bool = typer.Option(False, "--clear", help="Clear the error log and exit"),
):
    if clear:
        open(fallback, "w").close()
        print_box("Error log cleared.", title="Alex")
        raise SystemExit(0)

    if show:
        blocks = read_error_log_blocks(fallback)
        blocks = filter_error_blocks(blocks, since, grep)

        if not blocks:
            print_box("No error log found (after filters).", title="Alex")
            raise SystemExit(1)

        selected = "\n\n".join(blocks[-max(1, last):])
        print_box(Text(selected), title="Last error log(s)")
        raise SystemExit(0)

    err = None
    if not sys.stdin.isatty():
        err = sys.stdin.read().strip()

    if (not err) and text:
        err = " ".join(text).strip()

    if not err:
        blocks = read_error_log_blocks(fallback)
        blocks = filter_error_blocks(blocks, since, grep)
        if blocks:
            err = "\n\n".join(blocks[-max(1, last):])

    if not err:
        print_box(
            "No error text found.\n\nTry:\n"
            "  alex error\n"
            "  alex error -n 3 --show\n"
            "  alex error --show --grep ssh --since 2026-01-03\n"
            "  alex error --clear\n",
            title="Alex",
        )
        raise SystemExit(1)

    ensure_key()
    filters = []
    if since:
        filters.append(f"since={since}")
    if grep:
        filters.append(f"grep={grep}")
    finfo = f"Filters: {', '.join(filters)}\n\n" if filters else ""

    prompt = (
        f"Original command (optional): {cmd or '(unknown)'}\n\n"
        f"{finfo}"
        f"Error log:\n{err}\n"
    )
    data = call_responses_structured(prompt, intent="error_analysis")
    render_structured(data)

@app.command()
def service(
    name: str = typer.Argument(..., help="systemd unit name (e.g. ssh, ssh.service, nginx)"),
    apply: bool = typer.Option(False, "--apply", help="Run diagnostic commands (safe, read-only)"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Auto-confirm diagnostics"),
    rounds: int = typer.Option(3, "--rounds", help="How many diagnostic rounds max"),
):
    """Diagnose a systemd service (exists? running? why failing?)."""
    service_diagnose(name, apply=apply, yes=yes, max_rounds=rounds)


def main():
    if len(sys.argv) == 1:
        sys.argv.append("--help")
    app()
