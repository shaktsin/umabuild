from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from .core.doctor import run_doctor
from .core.generator import GenerationError, generate_app
from .core.llm.openai_provider import OpenAIProvider
from .core.patcher import apply_generation, ensure_generated_readme
from .core.runner import bootstrap_expo, run_expo_web
from .core.workspace import Workspace

app = typer.Typer(add_completion=False)
console = Console()


@app.command()
def doctor(
    no_expo: bool = typer.Option(False, "--no-expo", help="Skip Expo CLI check."),
) -> None:
    """Check system dependencies."""
    code = run_doctor(check_expo=not no_expo)
    raise typer.Exit(code)


@app.command()
def new(
    workspace: Path = typer.Option(..., "--workspace", exists=True, file_okay=False, dir_okay=True),
    provider: str = typer.Option("openai", "--provider"),
    model: str = typer.Option("gpt-4o-mini", "--model"),
    project_dir: str = typer.Option("app", "--project-dir"),
    no_install: bool = typer.Option(False, "--no-install"),
) -> None:
    """Create a new Expo app from README spec."""
    ws = Workspace(root=workspace, project_dir=project_dir)
    spec = ws.read_spec()
    ws.save_spec_snapshot(spec)

    if provider != "openai":
        console.print("[red]Only openai provider is implemented in this MVP.[/red]")
        raise typer.Exit(1)

    try:
        llm = OpenAIProvider()
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)

    console.print("[cyan]Bootstrapping Expo app...[/cyan]")
    bootstrap_expo(ws.root, ws.project_dir, no_install)

    console.print("[cyan]Generating app code...[/cyan]")
    try:
        result = generate_app(ws, llm, model=model, mode="new")
    except GenerationError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)

    apply_generation(ws, result.output, mode="new")
    ensure_generated_readme(ws)
    console.print("[green]Generation complete.[/green]")


@app.command()
def iterate(
    workspace: Path = typer.Option(..., "--workspace", exists=True, file_okay=False, dir_okay=True),
    provider: str = typer.Option("openai", "--provider"),
    model: str = typer.Option("gpt-4o-mini", "--model"),
    project_dir: str = typer.Option("app", "--project-dir"),
) -> None:
    """Iterate on an existing Expo app using README spec."""
    ws = Workspace(root=workspace, project_dir=project_dir)
    spec = ws.read_spec()
    ws.save_spec_snapshot(spec)

    if provider != "openai":
        console.print("[red]Only openai provider is implemented in this MVP.[/red]")
        raise typer.Exit(1)

    try:
        llm = OpenAIProvider()
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)

    console.print("[cyan]Regenerating managed files...[/cyan]")
    try:
        result = generate_app(ws, llm, model=model, mode="iterate")
    except GenerationError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)

    apply_generation(ws, result.output, mode="iterate")
    ensure_generated_readme(ws)
    console.print("[green]Iteration complete.[/green]")


@app.command()
def run(
    workspace: Path = typer.Option(..., "--workspace", exists=True, file_okay=False, dir_okay=True),
    project_dir: str = typer.Option("app", "--project-dir"),
    port: int | None = typer.Option(None, "--port"),
) -> None:
    """Run Expo web preview."""
    ws = Workspace(root=workspace, project_dir=project_dir)
    if not ws.project_path.exists():
        console.print("[red]Project directory not found. Run `umabuild new` first.[/red]")
        raise typer.Exit(1)
    console.print("[cyan]Starting Expo web preview...[/cyan]")
    url = run_expo_web(ws.project_path, port=port)
    if url:
        console.print(f"[green]Preview URL: {url}[/green]")
    else:
        console.print("[yellow]Could not detect URL. Check the Expo output above.[/yellow]")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
