from pathlib import Path

from umabuild.core.generator import GenerationOutput, GeneratedFile
from umabuild.core.patcher import apply_generation
from umabuild.core.workspace import Workspace


def test_iterate_only_overwrites_managed(tmp_path: Path) -> None:
    project = tmp_path / "app"
    project.mkdir()
    ws = Workspace(root=tmp_path)
    ws.save_managed(["App.tsx"])

    (project / "App.tsx").write_text("old", encoding="utf-8")
    (project / "Extra.tsx").write_text("keep", encoding="utf-8")

    output = GenerationOutput(
        files=[
            GeneratedFile(path="App.tsx", content="new"),
            GeneratedFile(path="Extra.tsx", content="overwrite"),
        ],
        managed_paths=["App.tsx", "Extra.tsx"],
    )

    apply_generation(ws, output, mode="iterate")

    assert (project / "App.tsx").read_text(encoding="utf-8") == "new"
    assert (project / "Extra.tsx").read_text(encoding="utf-8") == "keep"
