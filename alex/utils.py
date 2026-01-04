import os
from rich.console import Console

from .auth import load_key_into_env_if_missing

console = Console()

def ensure_key():
    load_key_into_env_if_missing()
    if not os.getenv("OPENAI_API_KEY"):
        console.print("[bold red]Missing OPENAI_API_KEY.[/bold red]\nRun: alex auth")
        raise SystemExit(1)
