from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
import re
from pathlib import PurePosixPath

from pydantic import BaseModel, ValidationError
from rich.console import Console

from .llm.base import LLMProvider
from .workspace import Workspace

console = Console()

SYSTEM_PROMPT = """You are an expert Expo + React Native engineer.
Generate a minimal, working Expo app that runs on web.
Use only built-in React Native components (no extra UI kits).
Avoid native-only APIs unless necessary.
Prefer a single-screen or minimal navigation unless explicitly requested.

Baseline UI styling rules (mandatory):
1) Every screen must have safe-area handling and consistent padding (16-20) with vertical spacing (12-16).
2) Every screen must render a top header bar with title on the left, optional right action, and a subtle bottom divider.
3) Always include and use shared UI baseline files:
   - src/ui/theme.ts
   - src/ui/Screen.tsx
   - src/ui/AppHeader.tsx
4) No content flush to screen edges.
5) Inputs/buttons must be at least 44pt height with comfortable spacing.
6) Lists must use visually separated rows/cards (padding 12-16, radius ~12, subtle border/shadow).
7) Provide a friendly empty state with spacing.
8) Must work in Expo Web preview and iOS/Android.

Output MUST be strict JSON matching the schema provided.
"""

JSON_SCHEMA_DESC = """Return JSON with:
- files: array of { "path": "relative/path", "content": "..." }
- managed_paths: array of strings
- notes: optional string
"""


class GeneratedFile(BaseModel):
    path: str
    content: str


class GenerationOutput(BaseModel):
    files: list[GeneratedFile]
    managed_paths: list[str]
    notes: str | None = None


@dataclass
class GenerationResult:
    output: GenerationOutput
    raw: str


class GenerationError(RuntimeError):
    pass


REQUIRED_UI_FILES = {
    "src/ui/theme.ts",
    "src/ui/Screen.tsx",
    "src/ui/AppHeader.tsx",
}

IMPORT_PATTERN = re.compile(
    r"""(?:import\s+[^'"]*from\s+|import\s+|require\()\s*['"]([^'"]+)['"]""",
    re.MULTILINE,
)

ASSET_EXTS = [".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp", ".json"]
CODE_EXTS = [".ts", ".tsx", ".js", ".jsx"]


def _build_user_prompt(spec_text: str, summary: dict, managed: dict[str, str]) -> str:
    managed_section = "\n".join(
        f"- {path}:\n```\n{content}\n```" for path, content in managed.items()
    )
    managed_block = managed_section if managed_section else "(none)"
    return "\n".join(
        [
            "App spec (README.md):",
            "```",
            spec_text,
            "```",
            "\nStructured summary:",
            json.dumps(summary, indent=2),
            "\nCurrently managed files and contents:",
            managed_block,
            "\nConstraints:",
            "- Output strict JSON only",
            "- Keep code minimal and runnable",
            "- Ensure App.tsx uses functional components",
            "\n" + JSON_SCHEMA_DESC,
        ]
    )


def _parse_output(raw: str) -> GenerationOutput:
    data = json.loads(raw)
    return GenerationOutput.model_validate(data)


def _validate_required_files(output: GenerationOutput) -> None:
    file_paths = {f.path for f in output.files}
    managed_paths = set(output.managed_paths)
    missing_files = REQUIRED_UI_FILES - file_paths
    missing_managed = REQUIRED_UI_FILES - managed_paths
    if missing_files or missing_managed:
        details = []
        if missing_files:
            details.append(f"missing files: {sorted(missing_files)}")
        if missing_managed:
            details.append(f"missing managed_paths: {sorted(missing_managed)}")
        raise GenerationError("Required UI baseline files not included: " + "; ".join(details))


def _collect_relative_imports(path: str, content: str) -> set[str]:
    rels: set[str] = set()
    for match in IMPORT_PATTERN.finditer(content):
        target = match.group(1)
        if target.startswith((".", "/")):
            rels.add(target)
    return rels


def _candidate_paths(base_dir: PurePosixPath, ref: str) -> list[str]:
    ref_path = PurePosixPath(ref)
    if ref.startswith("/"):
        resolved = ref_path.relative_to("/")
    else:
        resolved = (base_dir / ref_path)
    candidates: list[str] = []
    if resolved.suffix:
        candidates.append(resolved.as_posix())
    else:
        for ext in CODE_EXTS + ASSET_EXTS:
            candidates.append(resolved.with_suffix(ext).as_posix())
        for ext in CODE_EXTS:
            candidates.append((resolved / f"index{ext}").as_posix())
    return candidates


def _validate_imports(
    workspace: Workspace, output: GenerationOutput, mode: str
) -> None:
    output_paths = {f.path for f in output.files}
    disk_paths: set[str] = set()
    if mode == "iterate" and workspace.project_path.exists():
        for file_path in workspace.project_path.rglob("*"):
            if file_path.is_file():
                disk_paths.add(file_path.relative_to(workspace.project_path).as_posix())
    available = output_paths | disk_paths

    missing: set[str] = set()
    for file in output.files:
        base_dir = PurePosixPath(file.path).parent
        for ref in _collect_relative_imports(file.path, file.content):
            candidates = _candidate_paths(base_dir, ref)
            if not any(candidate in available for candidate in candidates):
                missing.add(f"{file.path} -> {ref}")
    if missing:
        missing_list = "; ".join(sorted(missing))
        raise GenerationError(
            "Missing referenced files for imports/assets: " + missing_list
        )


def generate_app(
    workspace: Workspace,
    provider: LLMProvider,
    model: str,
    mode: str,
    temperature: float = 0.2,
) -> GenerationResult:
    spec_text = workspace.read_spec()
    summary = workspace.extract_summary(spec_text)
    managed_paths = workspace.load_managed() if mode == "iterate" else []

    managed_contents: dict[str, str] = {}
    if mode == "iterate":
        for path in managed_paths:
            file_path = workspace.project_path / path
            if file_path.exists():
                managed_contents[path] = file_path.read_text(encoding="utf-8")

    messages: list[dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": _build_user_prompt(spec_text, summary, managed_contents),
        },
    ]

    for attempt in range(3):
        raw = provider.generate(messages=messages, model=model, temperature=temperature)
        workspace.log_generation(
            {
                "provider": provider.__class__.__name__,
                "model": model,
                "messages": messages,
                "response_raw": raw,
                "attempt": attempt + 1,
            }
        )
        try:
            output = _parse_output(raw)
            _validate_required_files(output)
            _validate_imports(workspace, output, mode)
            return GenerationResult(output=output, raw=raw)
        except (json.JSONDecodeError, ValidationError) as exc:
            if attempt >= 2:
                raise GenerationError(
                    "Model output was not valid JSON after retries. "
                    "Check the generation_log.jsonl for details."
                ) from exc
            fix_prompt = (
                "Your previous response was invalid. "
                "Return ONLY strict JSON that matches the schema. "
                "Do not include markdown or explanations.\n"
                f"Invalid output:\n{raw}"
            )
            messages.append({"role": "user", "content": fix_prompt})
        except GenerationError as exc:
            if attempt >= 2:
                raise
            fix_prompt = (
                "Your previous response is invalid. "
                "Return ONLY strict JSON that matches the schema, includes ALL required files, "
                "and ensures all imported files/assets exist.\n"
                f"Error: {exc}\n"
                f"Invalid output:\n{raw}"
            )
            messages.append({"role": "user", "content": fix_prompt})
    raise GenerationError("Model output was invalid.")
