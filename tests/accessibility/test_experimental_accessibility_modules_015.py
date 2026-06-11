from pathlib import Path

from sona.interpreter import SonaUnifiedInterpreter


ROOT = Path(__file__).resolve().parents[2]

EXPERIMENTAL_MODULES = [
    "interrupt",
    "hyperfocus",
    "priority",
    "drift",
    "scaffold",
    "reentry",
    "reward",
    "context",
    "momentum",
    "rotate",
    "start",
    "alias",
    "phonetic",
    "visual",
    "symbol",
    "sequence",
    "memory",
    "contrast",
    "template",
    "spoken",
    "pattern",
    "trace",
    "transition",
    "detail",
    "anchor",
    "overload",
    "mono",
    "system",
    "mastery",
    "shutdown",
    "energy",
    "narrative",
    "journal",
    "adapt",
]


def call(fn, *args):
    if hasattr(fn, "call"):
        return fn.call(list(args), {})
    return fn(*args)


def load(name):
    interp = SonaUnifiedInterpreter(project_root=ROOT)
    return interp.module_system.import_module(name)


def test_experimental_modules_import_and_report_local_status():
    for name in EXPERIMENTAL_MODULES:
        module = load(name)
        status = call(module.status)
        assert status["local_only"] is True
        assert "experimental_accessibility" in status


def test_adhd_experimental_modules_have_real_behavior():
    interrupt = load("interrupt")
    call(interrupt.configure, {"experimental_accessibility": False})
    assert call(interrupt.notice, "pause")["severity"] == "info"
    assert call(interrupt.queue, "pause")["requires_opt_in"] is True
    call(interrupt.configure, {"experimental_accessibility": True})
    assert call(interrupt.queue, "pause")["ok"] is True

    assert load("hyperfocus") and call(load("hyperfocus").check, 120)["risk"] == "high"
    assert call(load("priority").top, [{"name": "a", "priority": 1}, {"name": "b", "priority": 3}])["name"] == "b"
    assert call(load("drift").detect, [{"type": "switch"}, {"type": "work"}])["drift"] is True
    assert len(call(load("scaffold").steps, "ship", 2)) == 2
    assert call(load("reentry").card, "release")["next_step"] == "Choose the next visible action."

    reward = load("reward")
    call(reward.configure, {"experimental_accessibility": False})
    assert call(reward.log, "test")["requires_opt_in"] is True
    call(reward.configure, {"experimental_accessibility": True})
    assert call(reward.log, "test", 2)["total"] >= 2

    context = load("context")
    call(context.configure, {"experimental_accessibility": False})
    assert call(context.save, "task")["requires_opt_in"] is True
    call(context.configure, {"experimental_accessibility": True})
    assert call(context.save, "task", {"next": "test"})["ok"] is True
    assert call(context.current, "task")["details"]["next"] == "test"

    assert call(load("momentum").score, 1, 4)["percent"] == 25.0
    assert call(load("rotate").plan, ["a", "b", "c"], 1) == ["b", "c", "a"]
    assert "Open" in call(load("start").next, "tests")


def test_dyslexia_experimental_modules_have_real_behavior():
    assert call(load("alias").apply, "run spec", {"spec": "test"}) == "run test"
    assert call(load("phonetic").spell, "testing")
    assert call(load("visual").highlight, "alpha beta alpha", "alpha")["positions"] == [0, 11]
    assert call(load("symbol").explain, "==") == "equality comparison"
    assert call(load("sequence").check, [1, 1, 2])["duplicates"] == [1]

    memory = load("memory")
    call(memory.configure, {"experimental_accessibility": False})
    assert call(memory.store, "token", "meaning")["requires_opt_in"] is True
    call(memory.configure, {"experimental_accessibility": True})
    assert call(memory.store, "token", "meaning")["ok"] is True
    assert call(memory.recall, "token")["value"] == "meaning"
    assert call(memory.search, "token")["local_only"] is True

    assert call(load("contrast").ratio, "#000000", "#ffffff")["ok"] is True
    assert call(load("template").fill, "Hello {name}", {"name": "Sona"}) == "Hello Sona"
    assert call(load("spoken").script, "One. Two!") == ["One", "Two"]


def test_autism_experimental_modules_have_real_behavior():
    assert call(load("pattern").detect, [1, 2, 1, 2])["repeats"] is True
    assert call(load("trace").steps, ["open", "run"])[1]["step"] == 2
    assert call(load("transition").checklist, "edit", "test")["to"] == "test"
    assert "2 detail" in call(load("detail").expand, "api", {"a": 1, "b": 2})["summary"]

    anchor = load("anchor")
    call(anchor.configure, {"experimental_accessibility": False})
    assert call(anchor.set, "safe", "home")["requires_opt_in"] is True
    call(anchor.configure, {"experimental_accessibility": True})
    assert call(anchor.set, "safe", "home")["ok"] is True
    assert call(anchor.get, "safe")["value"] == "home"

    assert call(load("overload").check, ["noise", "light", "task"])["overloaded"] is True
    assert call(load("mono").focus, "debug")["mode"] == "single-thread"
    assert call(load("system").map, "app", ["cli"])["edges"] == [{"from": "app", "to": "cli"}]
    assert len(call(load("mastery").plan, "testing", 2)) == 2

    shutdown = load("shutdown")
    call(shutdown.configure, {"experimental_accessibility": False})
    assert call(shutdown.log, ["noise"])["requires_opt_in"] is True
    call(shutdown.configure, {"experimental_accessibility": True})
    assert call(shutdown.log, ["noise"])["ok"] is True


def test_cross_profile_experimental_modules_have_real_behavior():
    assert call(load("energy").check, 2, 10)["state"] == "low"
    assert "What happened" in call(load("narrative").frame, "build failed")["frame"]

    journal = load("journal")
    call(journal.configure, {"experimental_accessibility": False})
    assert call(journal.save, "note", "body")["requires_opt_in"] is True
    call(journal.configure, {"experimental_accessibility": True})
    assert call(journal.save, "note", "body")["ok"] is True
    assert call(journal.recent, 1)[0]["response"] == "body"

    adapt = load("adapt")
    call(adapt.configure, {"experimental_accessibility": False})
    assert call(adapt.set_preferences, "local", {"pace": "guided"})["requires_opt_in"] is True
    call(adapt.configure, {"experimental_accessibility": True})
    assert call(adapt.set_preferences, "local", {"pace": "guided"})["ok"] is True
    assert call(adapt.suggest, "dyslexia", "dense text")["suggestion"] == "increase spacing and chunk text"
