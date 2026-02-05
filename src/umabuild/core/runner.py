from __future__ import annotations

import re
import subprocess
from pathlib import Path

from rich.console import Console

console = Console()

URL_PATTERN = re.compile(r"(http://localhost:\d+|http://127\.0\.0\.1:\d+)")


def _stream_command(cmd: list[str], cwd: Path | None = None) -> str:
    process = subprocess.Popen(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    last_output = ""
    if not process.stdout:
        return ""
    for line in process.stdout:
        console.print(line.rstrip())
        last_output += line
    process.wait()
    if process.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")
    return last_output


def bootstrap_expo(workspace_root: Path, project_dir: str, no_install: bool) -> None:
    target = workspace_root / project_dir
    if target.exists():
        return
    cmd = [
        "npx",
        "create-expo-app",
        project_dir,
        "--template",
        "blank",
    ]
    if no_install:
        cmd.append("--no-install")
    _stream_command(cmd, cwd=workspace_root)


def _needs_web_deps(output: str) -> bool:
    return "react-dom" in output and "react-native-web" in output and "expo install" in output


def _needs_ts_deps(output: str) -> bool:
    return "TypeScript" in output and "typescript" in output and "@types/react" in output


def _needs_async_storage(output: str) -> bool:
    return "@react-native-async-storage/async-storage" in output and "Unable to resolve" in output


def _detect_missing_deps(output: str) -> list[str] | None:
    if _needs_web_deps(output):
        return ["react-dom", "react-native-web"]
    if _needs_ts_deps(output):
        return ["typescript", "@types/react"]
    if _needs_async_storage(output):
        return ["@react-native-async-storage/async-storage"]
    return None


def run_expo_web(project_root: Path, port: int | None = None) -> str | None:
    cmd = ["npx", "expo", "start", "--web"]
    if port:
        cmd.extend(["--port", str(port)])
    process = subprocess.Popen(
        cmd,
        cwd=str(project_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if not process.stdout:
        return None
    found_url = None
    output = ""
    to_install: list[str] | None = None
    for line in process.stdout:
        console.print(line.rstrip())
        output += line
        if not found_url:
            match = URL_PATTERN.search(line)
            if match:
                found_url = match.group(1)
        if not to_install:
            to_install = _detect_missing_deps(line) or _detect_missing_deps(output)
            if to_install:
                break
    if to_install:
        process.terminate()
        process.wait()
        console.print("[yellow]Installing missing dependencies...[/yellow]")
        _stream_command(["npx", "expo", "install", *to_install], cwd=project_root)
        return run_expo_web(project_root, port=port)
    process.wait()
    if process.returncode != 0:
        to_install = _detect_missing_deps(output)
        if to_install:
            console.print("[yellow]Installing missing dependencies...[/yellow]")
            _stream_command(["npx", "expo", "install", *to_install], cwd=project_root)
            return run_expo_web(project_root, port=port)
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")
    return found_url
