from pathlib import Path

import pytest

from sona.interpreter import SonaUnifiedInterpreter


ROOT = Path(__file__).resolve().parents[2]


def call(fn, *args):
    if hasattr(fn, "call"):
        return fn.call(list(args), {})
    return fn(*args)


def load(name):
    interp = SonaUnifiedInterpreter(project_root=ROOT)
    return interp.module_system.import_module(name)


def test_format_module_surface():
    fmt = load("format")
    assert call(fmt.number, 3.14159, 2) == "3.14"
    assert call(fmt.integer, 7.8) == "7"
    assert call(fmt.percent, 0.125, 1) == "12.5%"
    assert call(fmt.pad_left, "7", 3, "0") == "007"
    assert call(fmt.pad_right, "x", 3, ".") == "x.."
    assert call(fmt.center, "x", 3, ".") == ".x."
    assert "Sona" in call(fmt.table, [["Sona", 15]], ["name", "version"])
    assert call(fmt.progress, 1, 2, 4) == "[##--] 50%"
    assert call(fmt.truncate, "abcdef", 5) == "ab..."


def test_color_module_respects_disable_and_strips_ansi(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    color = load("color")
    assert call(color.enable) is False
    assert call(color.is_enabled) is False
    assert call(color.red, "stop") == "stop"
    assert call(color.strip, "\x1b[31mstop\x1b[0m") == "stop"
    assert call(color.reset) == ""


def test_assert_module_surface():
    assertions = load("assert")
    assert call(assertions.equal, 1, 1) is True
    assert call(assertions.not_equal, 1, 2) is True
    assert call(assertions.true, True) is True
    assert call(assertions.false, False) is True
    assert call(assertions.contains, [1, 2], 2) is True
    with pytest.raises(AssertionError):
        call(assertions.fail, "boom")


def test_url_module_surface():
    url = load("url")
    parsed = call(url.parse, "https://example.com/path?q=sona")
    assert parsed["scheme"] == "https"
    assert parsed["host"] == "example.com"
    assert call(url.build, {"scheme": "https", "host": "example.com", "path": "/x"}) == "https://example.com/x"
    assert call(url.encode, "hello world") == "hello%20world"
    assert call(url.decode, "hello%20world") == "hello world"
    assert call(url.query_encode, {"a": "1", "b": "2"}) in {"a=1&b=2", "b=2&a=1"}
    assert call(url.query_decode, "a=1&a=2") == {"a": ["1", "2"]}
    assert call(url.join, "https://example.com/a/", "b") == "https://example.com/a/b"


def test_pipe_module_surface():
    pipe = load("pipe")
    assert call(pipe.map, [1, 2, 3], lambda value: value * 2) == [2, 4, 6]
    assert call(pipe.filter, [1, 2, 3], lambda value: value > 1) == [2, 3]
    assert call(pipe.reduce, [1, 2, 3], lambda acc, value: acc + value, 0) == 6
    assert call(pipe.each, [1, 2], lambda value: value) == [1, 2]
    assert call(pipe.take, [1, 2, 3], 2) == [1, 2]
    assert call(pipe.drop, [1, 2, 3], 1) == [2, 3]
    assert call(pipe.unique, [1, 1, 2]) == [1, 2]


def test_intent_focus_and_log_are_in_memory():
    intent = load("intent")
    call(intent.clear_all)
    assert call(intent.set, "release", "Ship 0.15.0") == {
        "name": "release",
        "description": "Ship 0.15.0",
    }
    assert call(intent.has, "release") is True
    assert call(intent.get, "release") == "Ship 0.15.0"
    assert call(intent.clear, "release") is True

    focus = load("focus")
    call(focus.clear)
    assert call(focus.is_active) is False
    assert call(focus.begin, "docs", "Write references")["name"] == "docs"
    assert call(focus.is_active) is True
    assert call(focus.current)["description"] == "Write references"
    assert call(focus.end, "done")["summary"] == "done"
    assert len(call(focus.history)) == 1

    log = load("log")
    call(log.clear)
    assert call(log.set_level, "debug") == "debug"
    assert call(log.set_format, "json") == "json"
    event = call(log.debug, "utility", {"password": "hidden"})
    assert event["fields"]["password"] == "[redacted]"
