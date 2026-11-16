import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import pytest
import asker


@pytest.fixture(autouse=True)
def _no_user_mods(tmp_path, monkeypatch):
    """Never read the real mod folder in tests."""
    monkeypatch.setattr(asker, "MOD_ROOT", tmp_path / "mods")
