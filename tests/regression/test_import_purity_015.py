import socket
import time
from pathlib import Path

import pytest

from sona.interpreter import SonaUnifiedInterpreter


PUBLIC_IMPORTS = [
    "fs",
    "path",
    "csv",
    "format",
    "color",
    "assert",
    "url",
    "pipe",
    "intent",
    "focus",
    "log",
    "profile",
    "guardian",
    "simplify",
    "breadcrumb",
    "flow",
    "explain",
    "pace",
    "affirm",
    "chunk",
    "timer",
    "noise",
    "tone",
    "readability",
    "linewidth",
    "mirror",
    "chunk_read",
    "contract",
    "boundary",
    "routine",
    "strict",
    "certainty",
    "sensory",
]


def snapshot(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


@pytest.mark.parametrize("module_name", PUBLIC_IMPORTS)
def test_public_smod_imports_are_side_effect_safe(tmp_path, monkeypatch, module_name):
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))

    def fail_sleep(*_args, **_kwargs):
        raise AssertionError("public .smod import attempted to sleep")

    def fail_connect(*_args, **_kwargs):
        raise AssertionError("public .smod import attempted network access")

    monkeypatch.setattr(time, "sleep", fail_sleep)
    monkeypatch.setattr(socket.socket, "connect", fail_connect, raising=False)

    interp = SonaUnifiedInterpreter(project_root=project)
    before_project = snapshot(project)
    before_home = snapshot(home)
    interp.module_system.import_module(module_name)

    assert snapshot(project) == before_project
    assert snapshot(home) == before_home
