import sys
from pathlib import Path

from sona.interpreter import SonaUnifiedInterpreter

sys.path.append(str(Path(__file__).resolve().parent))

from _surface_015 import ROOT  # noqa: E402


def call(fn, *args):
    if hasattr(fn, "call"):
        return fn.call(list(args), {})
    return fn(*args)


def load(name, project_root=ROOT):
    interp = SonaUnifiedInterpreter(project_root=project_root)
    return interp.module_system.import_module(name)


def test_path_handles_windows_and_posix_style_inputs():
    path = load("path")

    assert call(path.basename, r"C:\sona\project\app.sona") in {
        r"C:\sona\project\app.sona",
        "app.sona",
    }
    assert call(path.basename, "/sona/project/app.sona") == "app.sona"
    assert call(path.extension, "/sona/project/app.sona") == ".sona"
    assert call(path.relative, "a/b/c.sona", "a").replace("\\", "/") == "b/c.sona"


def test_csv_newline_behavior_and_temp_paths(tmp_path):
    csv = load("csv", tmp_path)
    target = tmp_path / "rows.csv"
    rows = [{"name": "Sona", "score": "15"}, {"name": "Guardian", "score": "1"}]

    assert call(csv.write, str(target), rows, ",")["success"] is True
    contents = target.read_text(encoding="utf-8")
    assert "Sona" in contents
    parsed = call(csv.read, str(target), ",")
    assert parsed["records"] == rows


def test_color_disable_and_no_color_are_terminal_safe(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    color = load("color")

    assert call(color.enable) is False
    assert call(color.is_enabled) is False
    assert call(color.red, "stop") == "stop"
    assert call(color.strip, "\x1b[31mstop\x1b[0m") == "stop"
