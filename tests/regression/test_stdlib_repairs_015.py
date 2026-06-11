from pathlib import Path

from sona.interpreter import SonaUnifiedInterpreter


ROOT = Path(__file__).resolve().parents[2]


def call(fn, *args):
    if hasattr(fn, "call"):
        return fn.call(list(args), {})
    return fn(*args)


def load(name, project_root=ROOT):
    interp = SonaUnifiedInterpreter(project_root=project_root)
    return interp.module_system.import_module(name)


def test_date_aliases_work():
    date = load("date")
    assert isinstance(call(date.today, "UTC"), str)
    assert "T" in call(date.now, "UTC")
    assert "+00:00" in call(date.utcnow)
    assert call(date.fromtimestamp, 0, "UTC") == "1970-01-01"
    assert call(date.from_timestamp, 0, "UTC") == "1970-01-01"


def test_path_stem_and_relative_aliases():
    path = load("path")
    assert call(path.stem, "folder/report.csv") == "report"
    assert call(path.relative, "a/b/c.txt", "a").replace("\\", "/") == "b/c.txt"
    assert call(path.relative_to, "a/b/c.txt", "a").replace("\\", "/") == "b/c.txt"


def test_csv_simple_delimiter_api(tmp_path):
    csv = load("csv", tmp_path)
    parsed = call(csv.parse, "name;score\nSona;15\n", ";")
    assert parsed["success"] is True
    assert parsed["row_count"] == 1
    rows = [{"name": "Sona", "score": "15"}]
    rendered = call(csv.stringify, rows, ";")
    assert rendered["success"] is True
    assert "Sona" in rendered["csv_data"]

    target = tmp_path / "scores.csv"
    written = call(csv.write, str(target), rows, ";")
    assert written["success"] is True
    read_back = call(csv.read, str(target), ";")
    assert read_back["success"] is True
    assert read_back["row_count"] >= 1


def test_log_profile_guardian_facades_have_real_behavior(tmp_path):
    log = load("log", tmp_path)
    call(log.clear)
    event = call(log.info, "started", {"token": "secret-value", "step": 1})
    assert event["level"] == "info"
    assert event["fields"]["token"] == "[redacted]"
    assert call(log.history, 1)[0]["message"] == "started"

    profile = load("profile", tmp_path)
    assert "adhd" in call(profile.available)
    assert call(profile.activate, "adhd")["active"] == ["adhd"]
    assert call(profile.reset)["active"] == []

    guardian = load("guardian", tmp_path)
    status = call(guardian.status, str(tmp_path))
    assert status["initialized"] is False
    initialized = call(guardian.init, str(tmp_path))
    assert initialized["status"] == "initialized"
    assert call(guardian.verify, str(tmp_path))["status"] == "ok"
