from pathlib import Path

import pytest

from umabuild.core.generator import GenerationError, generate_app
from umabuild.core.llm.base import LLMProvider
from umabuild.core.workspace import Workspace


class FakeProvider(LLMProvider):
    def __init__(self, outputs: list[str]):
        self.outputs = outputs
        self.calls = 0

    def generate(self, messages, model, temperature=0.2, **kwargs):
        out = self.outputs[self.calls]
        self.calls += 1
        return out


def test_json_retry_then_success(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# App", encoding="utf-8")
    provider = FakeProvider(
        [
            "not json",
            '{"files": [{"path": "App.tsx", "content": "ok"}], "managed_paths": ["App.tsx"]}',
        ]
    )
    ws = Workspace(root=tmp_path)
    result = generate_app(ws, provider, model="test", mode="new")
    assert result.output.files[0].path == "App.tsx"
    assert provider.calls == 2


def test_json_retry_fail(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# App", encoding="utf-8")
    provider = FakeProvider(["bad", "still bad", "nope"])
    ws = Workspace(root=tmp_path)
    with pytest.raises(GenerationError):
        generate_app(ws, provider, model="test", mode="new")
