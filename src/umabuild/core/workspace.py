from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

from rich.console import Console

console = Console()

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password)")
]
REDACT_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
]
JSON_SECRET_VALUE = re.compile(
    r'("(api[_-]?key|secret|token|password)"\\s*:\\s*")([^"]+)',
    re.IGNORECASE,
)


def _redact_text(text: str, extra_secrets: Iterable[str] | None = None) -> str:
    redacted = text
    for pattern in REDACT_PATTERNS:
        redacted = pattern.sub("***REDACTED***", redacted)
    redacted = JSON_SECRET_VALUE.sub(r'\\1***REDACTED***', redacted)
    if extra_secrets:
        for secret in extra_secrets:
            if secret:
                redacted = redacted.replace(secret, "***REDACTED***")
    return redacted


@dataclass
class Workspace:
    root: Path
    project_dir: str = "app"

    @property
    def readme_path(self) -> Path:
        return self.root / "README.md"

    @property
    def project_path(self) -> Path:
        return self.root / self.project_dir

    @property
    def meta_dir(self) -> Path:
        return self.root / ".umabuild"

    @property
    def spec_snapshot_path(self) -> Path:
        return self.meta_dir / "spec_snapshot.md"

    @property
    def managed_path(self) -> Path:
        return self.meta_dir / "managed.json"

    @property
    def log_path(self) -> Path:
        return self.meta_dir / "generation_log.jsonl"

    def ensure_meta(self) -> None:
        self.meta_dir.mkdir(parents=True, exist_ok=True)

    def read_spec(self) -> str:
        if not self.readme_path.exists():
            raise FileNotFoundError(f"Missing README spec at {self.readme_path}")
        text = self.readme_path.read_text(encoding="utf-8")
        if not text.strip():
            raise ValueError("README.md is empty. Please describe your app spec.")
        if self._contains_secrets(text):
            console.print("[yellow]Warning: README.md may contain secrets. Proceeding carefully.[/yellow]")
        return text

    def _contains_secrets(self, text: str) -> bool:
        return any(p.search(text) for p in SECRET_PATTERNS)

    def save_spec_snapshot(self, text: str) -> None:
        self.ensure_meta()
        self.spec_snapshot_path.write_text(text, encoding="utf-8")

    def load_managed(self) -> list[str]:
        if not self.managed_path.exists():
            return []
        try:
            data = json.loads(self.managed_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return [str(p) for p in data]
        except json.JSONDecodeError:
            return []
        return []

    def save_managed(self, paths: list[str]) -> None:
        self.ensure_meta()
        unique = sorted({p.replace("\\", "/") for p in paths})
        self.managed_path.write_text(json.dumps(unique, indent=2), encoding="utf-8")

    def log_generation(self, payload: dict) -> None:
        self.ensure_meta()
        extra = [os.getenv("OPENAI_API_KEY", "")]
        redacted = json.loads(_redact_text(json.dumps(payload), extra))
        redacted["ts"] = datetime.utcnow().isoformat() + "Z"
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(redacted) + "\n")

    def extract_summary(self, text: str) -> dict:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        app_name = None
        if lines and lines[0].startswith("#"):
            app_name = lines[0].lstrip("#").strip()
        screens = []
        features = []
        data = []
        current = None
        for line in lines:
            lower = line.lower()
            if lower.startswith("##") or lower.startswith("#"):
                header = lower.lstrip("#").strip()
                if "screen" in header:
                    current = "screens"
                elif "feature" in header:
                    current = "features"
                elif "data" in header or "storage" in header:
                    current = "data"
                else:
                    current = None
                continue
            if line.startswith("-") or line.startswith("*"):
                item = line.lstrip("-* ").strip()
                if current == "screens":
                    screens.append(item)
                elif current == "features":
                    features.append(item)
                elif current == "data":
                    data.append(item)
        return {
            "app_name": app_name or "MyApp",
            "screens": screens,
            "features": features,
            "data_storage_needs": data,
        }
