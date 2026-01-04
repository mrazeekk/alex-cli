from typing import Any, Dict

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

def print_box(renderable, title: str = "Alex"):
    console.print(
        Panel(
            renderable,
            title=f"[bold green]{title}[/bold green]",
            title_align="left",
            border_style="white",
            expand=False,
            padding=(1, 2),
        )
    )

def render_structured(data: Dict[str, Any]):
    summary = Text(data.get("summary", "").strip())

    steps = data.get("steps", [])
    steps_text = Text()
    if steps:
        for i, s in enumerate(steps, start=1):
            steps_text.append(f"{i}. {s}\n")
    else:
        steps_text.append("No steps provided.\n")

    cmds = data.get("commands", [])
    cmd_table = Table(show_header=True, header_style="bold")
    cmd_table.add_column("Command", overflow="fold")
    cmd_table.add_column("Why", overflow="fold")
    cmd_table.add_column("Risk", width=11)

    for c in cmds:
        risk = c.get("risk", "low")
        risk_style = {
            "low": "green",
            "medium": "yellow",
            "high": "red",
            "super_high": "bold red",
        }.get(risk, "white")
        cmd_table.add_row(c.get("cmd", ""), c.get("why", ""), Text(risk, style=risk_style))

    checks = data.get("checks", [])
    notes = data.get("notes", [])

    checks_text = Text()
    if checks:
        for c in checks:
            checks_text.append(f"• {c}\n")
    else:
        checks_text.append("• None\n")

    notes_text = Text()
    if notes:
        for n in notes:
            notes_text.append(f"• {n}\n")
    else:
        notes_text.append("• None\n")

    body = Table.grid(padding=(0, 1))
    body.add_row(Text("Summary", style="bold"))
    body.add_row(summary)
    body.add_row(Text(""))
    body.add_row(Text("Steps", style="bold"))
    body.add_row(steps_text)
    body.add_row(Text("Commands", style="bold"))
    body.add_row(cmd_table)
    body.add_row(Text("Checks", style="bold"))
    body.add_row(checks_text)
    body.add_row(Text("Notes", style="bold"))
    body.add_row(notes_text)

    print_box(body, title="Alex")
