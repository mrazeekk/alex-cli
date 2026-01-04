import os
from rich.console import Console

console = Console()

def ensure_key():
    if not os.getenv("OPENAI_API_KEY"):
        console.print("[bold red]Missing OPENAI_API_KEY environment variable.[/bold red]")
        raise SystemExit(1)
