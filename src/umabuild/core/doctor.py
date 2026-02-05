from __future__ import annotations

import shutil
import subprocess
import sys

from rich.console import Console

console = Console()


def _check_binary(name: str) -> bool:
    return shutil.which(name) is not None


def run_doctor(check_expo: bool = True) -> int:
    ok = True
    if sys.version_info < (3, 10):
        console.print("[red]Python 3.10+ is required.[/red]")
        ok = False
    else:
        console.print(f"[green]Python {sys.version_info.major}.{sys.version_info.minor} OK[/green]")

    for binary in ["node", "npx"]:
        if _check_binary(binary):
            console.print(f"[green]{binary} OK[/green]")
        else:
            console.print(f"[red]{binary} not found[/red]")
            ok = False

    if check_expo:
        try:
            result = subprocess.run(
                ["npx", "expo", "--version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=15,
            )
            if result.returncode == 0:
                console.print(f"[green]expo OK ({result.stdout.strip()})[/green]")
            else:
                console.print("[red]expo not available via npx[/red]")
                ok = False
        except subprocess.TimeoutExpired:
            console.print("[yellow]expo version check timed out (npx may be installing).[/yellow]")
        except FileNotFoundError:
            console.print("[red]npx not available[/red]")
            ok = False

    return 0 if ok else 1
