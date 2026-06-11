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


def test_cross_profile_accessibility_modules():
    simplify = load("simplify")
    assert "Check the value" in call(simplify.message, "UnexpectedError: Check the value.", "plain")
    assert call(simplify.steps, "failed") == [
        "Read the error message.",
        "Check the named file or module.",
        "Run the smallest relevant test again.",
    ]

    breadcrumb = load("breadcrumb")
    call(breadcrumb.clear)
    assert call(breadcrumb.add, "opened file", {"path": "main.sona"})["message"] == "opened file"
    assert call(breadcrumb.current)["fields"]["path"] == "main.sona"
    assert call(breadcrumb.format, "plain") == "- opened file"

    flow = load("flow")
    report = call(flow.check, {"task_switches": 1, "interruptions": 1, "uncertainty": 0.2})
    assert report["ok"] is True
    assert 0 <= report["score"] <= 1
    assert isinstance(call(flow.suggest, {"task_switches": 8}), list)

    explain = load("explain")
    assert "dict:" in call(explain.value, {"a": 1})
    assert "Module" in call(explain.module, "profile")

    pace = load("pace")
    assert call(pace.set, "guided") == "guided"
    assert call(pace.current) == "guided"
    assert call(pace.format, "first\nsecond") == "- first\n- second"

    affirm = load("affirm")
    call(affirm.enable)
    assert call(affirm.enabled) is True
    assert call(affirm.success, "tests passed")["message"] == "tests passed"
    assert call(affirm.disable) is False


def test_adhd_profile_accessibility_modules():
    chunk = load("chunk")
    assert call(chunk.items, [1, 2, 3, 4], 2) == [[1, 2], [3, 4]]
    assert call(chunk.text, "one two", 3) == ["one", "two"]
    assert call(chunk.resume, "missing") is None
    call(chunk.checkpoint, "release", {"step": 1})
    assert call(chunk.resume, "release") == {"step": 1}

    timer = load("timer")
    started = call(timer.start, "review", 1)
    assert started["name"] == "review"
    assert call(timer.remaining) >= 0
    assert call(timer.pause)["paused"] is True
    assert call(timer.resume)["paused"] is False
    assert call(timer.stop, "done")["summary"] == "done"

    noise = load("noise")
    assert call(noise.set_level, "focused") == "focused"
    events = [{"scope": "build"}, {"scope": "chat"}]
    call(noise.block, "chat")
    assert call(noise.filter, events) == [{"scope": "build"}]
    assert call(noise.reset) is True

    tone = load("tone")
    assert call(tone.set, "neutral") == "neutral"
    assert call(tone.neutralize, "Obviously you failed!") == "you failed."


def test_dyslexia_profile_accessibility_modules():
    readability = load("readability")
    score = call(readability.score, "short words")
    assert score["word_count"] == 2
    assert call(readability.identifier, "ambiguousName")["ok"] is True
    assert isinstance(call(readability.suggest, "ambiguousName"), list)

    linewidth = load("linewidth")
    assert call(linewidth.set, 20) == 20
    wrapped = call(linewidth.wrap, "alpha beta gamma delta epsilon")
    assert "\n" in wrapped
    assert call(linewidth.check, "alpha beta gamma delta epsilon")["ok"] is False

    mirror = load("mirror")
    assert any(pair["left"] == "=" for pair in call(mirror.pairs))
    assert call(mirror.check, "a = b == c") != []
    assert "assignment" in call(mirror.explain, "=")

    chunk_read = load("chunk_read")
    assert call(chunk_read.text, "one two three four", 2) == ["one two", "three four"]
    assert call(chunk_read.sections, ["one two", "three four"]) == ["one two", "three four"]
    assert call(chunk_read.current) == "one two"
    assert call(chunk_read.next) == "three four"
    assert call(chunk_read.previous) == "one two"
    assert call(chunk_read.reset) is True


def test_autism_profile_accessibility_modules():
    contract = load("contract")
    assert call(contract.require, True, "ok") is True
    assert call(contract.type, 1, "number", "count") is True
    assert call(contract.range, 2, 1, 3, "count") is True
    assert call(contract.non_empty, [1], "items") is True
    assert call(contract.equal, "a", "a") is True
    with pytest.raises(AssertionError):
        call(contract.ensure, False, "must pass")

    boundary = load("boundary")
    call(boundary.create, "safe", ["read", "write:docs"])
    assert call(boundary.activate, "safe")["name"] == "safe"
    assert call(boundary.check, "read") is True
    assert call(boundary.allow, "write", "docs") is True
    assert call(boundary.deny, "delete") is True
    assert call(boundary.check, "delete") is False
    assert call(boundary.deactivate) is True

    routine = load("routine")
    call(routine.reset)
    assert call(routine.define, "release", ["test", "tag"])["steps"] == ["test", "tag"]
    assert call(routine.start, "release")["current_step"] == "test"
    assert call(routine.next)["current_step"] == "tag"
    assert call(routine.complete)["complete"] is True

    strict = load("strict")
    assert call(strict.enable) is True
    assert call(strict.is_enabled) is True
    assert call(strict.check, {"ok": True})["ok"] is True
    assert call(strict.disable) is False

    certainty = load("certainty")
    call(certainty.clear)
    assert call(certainty.check, {"certainty": "low"})["severity"] == "warning"
    assert call(certainty.add, "assumption", "needs review")["severity"] == "info"
    assert len(call(certainty.report)) == 1

    sensory = load("sensory")
    assert call(sensory.enable) is True
    assert call(sensory.is_enabled) is True
    assert call(sensory.apply, "IMPORTANT!!! read now") == "IMPORTANT! read now"
    assert call(sensory.disable) is False
