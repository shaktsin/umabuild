from pathlib import Path

import pytest

from umabuild.core.workspace import Workspace


def test_read_spec(tmp_path: Path) -> None:
    ws = Workspace(root=tmp_path)
    with pytest.raises(FileNotFoundError):
        ws.read_spec()
    readme = tmp_path / "README.md"
    readme.write_text("# My App\n", encoding="utf-8")
    assert "My App" in ws.read_spec()
