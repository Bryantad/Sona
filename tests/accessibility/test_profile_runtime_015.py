import json
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

from sona.interpreter import SonaUnifiedInterpreter
from sona.stdlib import native_profile


ROOT = Path(__file__).resolve().parents[2]


def call(fn, *args):
    if hasattr(fn, "call"):
        return fn.call(list(args), {})
    return fn(*args)


def load_modules(*names):
    interp = SonaUnifiedInterpreter(project_root=ROOT)
    return [interp.module_system.import_module(name) for name in names]


@pytest.fixture(scope="module")
def runtime_modules():
    names = [
        "profile",
        "pace",
        "noise",
        "flow",
        "linewidth",
        "readability",
        "strict",
        "sensory",
    ]
    modules = load_modules(*names)
    return dict(zip(names, modules))


@pytest.fixture(autouse=True)
def reset_profile_runtime_state():
    native_profile.profile_reset()
    yield
    native_profile.profile_reset()


def snapshot(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def test_available_profiles_include_manifest_profiles(runtime_modules):
    profile = runtime_modules["profile"]

    available = call(profile.available)

    assert available == [
        "cross-profile",
        "adhd",
        "dyslexia",
        "autism",
        "low-stimulation",
        "custom",
    ]


def test_profile_presets_modify_actual_public_runtime_modules(runtime_modules):
    profile = runtime_modules["profile"]
    pace = runtime_modules["pace"]
    noise = runtime_modules["noise"]
    flow = runtime_modules["flow"]
    linewidth = runtime_modules["linewidth"]
    readability = runtime_modules["readability"]
    strict = runtime_modules["strict"]
    sensory = runtime_modules["sensory"]
    call(profile.reset)

    call(profile.activate, "adhd")
    assert call(pace.current) == "guided"
    assert call(noise.current_level) == "focused"
    assert call(flow.configure, {})["max_switches"] == 3

    call(profile.activate, "dyslexia")
    assert call(linewidth.current) == 72
    assert "long" in call(readability.identifier, "abcdefghijklmnopqrstuvwxy")["issues"]

    call(profile.activate, "autism")
    assert call(strict.is_enabled) is True
    assert call(sensory.is_enabled) is True
    assert call(sensory.apply, "IMPORTANT!!!") == "IMPORTANT!"

    call(profile.activate, "low-stimulation")
    assert call(pace.current) == "low-stimulation"
    assert call(noise.current_level) == "minimal"
    assert call(sensory.is_enabled) is True

    call(profile.activate, "cross-profile")
    assert call(pace.current) == "guided"
    assert call(flow.configure, {})["max_switches"] == 4


def test_custom_profile_only_applies_explicit_options(runtime_modules):
    profile = runtime_modules["profile"]
    pace = runtime_modules["pace"]
    noise = runtime_modules["noise"]
    linewidth = runtime_modules["linewidth"]
    strict = runtime_modules["strict"]
    sensory = runtime_modules["sensory"]
    call(profile.reset)

    current = call(profile.activate, "custom")

    assert current["active"] == ["custom"]
    assert call(pace.current) == "balanced"
    assert call(noise.current_level) == "normal"
    assert call(linewidth.current) == 80
    assert call(strict.is_enabled) is False
    assert call(sensory.is_enabled) is False

    configured = call(
        profile.configure,
        {
            "pace_mode": "guided",
            "noise_level": "focused",
            "linewidth": 72,
            "max_identifier_length": 24,
            "strict": True,
            "sensory": True,
            "flow": {"max_switches": 2},
            "unknown_future_option": "preserved",
        },
    )

    assert configured["options"]["unknown_future_option"] == "preserved"
    assert call(pace.current) == "guided"
    assert call(noise.current_level) == "focused"
    assert call(linewidth.current) == 72
    assert call(strict.is_enabled) is True
    assert call(sensory.is_enabled) is True


def test_activate_many_precedence_and_reset_restore_baseline(runtime_modules):
    profile = runtime_modules["profile"]
    pace = runtime_modules["pace"]
    noise = runtime_modules["noise"]
    flow = runtime_modules["flow"]
    linewidth = runtime_modules["linewidth"]
    readability = runtime_modules["readability"]
    strict = runtime_modules["strict"]
    sensory = runtime_modules["sensory"]
    call(profile.reset)

    current = call(profile.activate_many, ["adhd", "dyslexia", "autism"])

    assert current["active"] == ["adhd", "dyslexia", "autism"]
    assert call(pace.current) == "guided"
    assert call(noise.current_level) == "focused"
    assert call(linewidth.current) == 72
    assert call(flow.configure, {})["max_switches"] == 3
    assert call(strict.is_enabled) is True
    assert call(sensory.is_enabled) is True

    reset = call(profile.reset)

    assert reset["active"] == []
    assert reset["persistent"] is False
    assert reset["local_only"] is True
    assert call(pace.current) == "balanced"
    assert call(noise.current_level) == "normal"
    assert call(linewidth.current) == 80
    assert call(readability.configure, {})["max_identifier_length"] == 32
    assert call(flow.configure, {}) == {"max_switches": 5, "max_errors": 3}
    assert call(strict.is_enabled) is False
    assert call(sensory.is_enabled) is False


def test_profile_current_exposes_runtime_visibility(runtime_modules):
    profile = runtime_modules["profile"]
    call(profile.reset)
    current = call(profile.activate, "low-stimulation")

    assert current["active"] == ["low-stimulation"]
    assert current["local_only"] is True
    assert current["persistent"] is False
    assert current["runtime"]["pace_mode"] == "low-stimulation"
    assert current["runtime"]["noise_level"] == "minimal"
    assert current["runtime"]["linewidth"] == 80
    assert current["runtime"]["readability"]["max_identifier_length"] == 32
    assert current["runtime"]["strict_enabled"] is False
    assert current["runtime"]["sensory_enabled"] is True
    assert current["runtime"]["flow"] == {"max_switches": 5, "max_errors": 3}


@pytest.mark.parametrize(
    "options",
    [
        {"pace_mode": "bad-value"},
        {"noise_level": "bad-value"},
        {"linewidth": -1},
        {"max_identifier_length": 0},
        {"strict": "yes"},
        {"sensory": "yes"},
        {"flow": {"max_switches": -1}},
    ],
)
def test_invalid_known_runtime_options_do_not_mutate_runtime(runtime_modules, options):
    profile = runtime_modules["profile"]
    pace = runtime_modules["pace"]
    noise = runtime_modules["noise"]
    linewidth = runtime_modules["linewidth"]
    strict = runtime_modules["strict"]
    sensory = runtime_modules["sensory"]
    call(profile.reset)
    call(profile.activate, "adhd")
    before = call(profile.current)

    with pytest.raises(ValueError):
        call(profile.configure, options)

    after = call(profile.current)
    assert after == before
    assert call(pace.current) == before["runtime"]["pace_mode"]
    assert call(noise.current_level) == before["runtime"]["noise_level"]
    assert call(linewidth.current) == before["runtime"]["linewidth"]
    assert call(strict.is_enabled) == before["runtime"]["strict_enabled"]
    assert call(sensory.is_enabled) == before["runtime"]["sensory_enabled"]


def test_profile_import_is_side_effect_safe(tmp_path, monkeypatch):
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))

    def fail_sleep(*_args, **_kwargs):
        raise AssertionError("profile import attempted to sleep")

    def fail_connect(*_args, **_kwargs):
        raise AssertionError("profile import attempted network access")

    monkeypatch.setattr(time, "sleep", fail_sleep)
    monkeypatch.setattr(socket.socket, "connect", fail_connect, raising=False)

    interp = SonaUnifiedInterpreter(project_root=project)
    before_project = snapshot(project)
    before_home = snapshot(home)
    interp.module_system.import_module("profile")

    assert snapshot(project) == before_project
    assert snapshot(home) == before_home


def test_profile_state_is_not_persisted_across_processes(runtime_modules):
    profile = runtime_modules["profile"]
    call(profile.reset)
    call(profile.activate, "adhd")

    code = f"""
import json
from pathlib import Path
from sona.interpreter import SonaUnifiedInterpreter

interp = SonaUnifiedInterpreter(project_root=Path({str(ROOT)!r}))
profile = interp.module_system.import_module("profile")
current = profile.current.call([], {{}})
print(json.dumps(current, sort_keys=True))
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    current = json.loads(result.stdout)

    assert current["active"] == []
    assert current["runtime"]["pace_mode"] == "balanced"
    assert current["runtime"]["noise_level"] == "normal"
    assert current["persistent"] is False
    assert current["local_only"] is True


def test_015_roadmap_docs_exist_without_completed_independence_claims():
    roadmap_docs = [
        "docs/roadmap/SONA_NATIVE_INDEPENDENCE.md",
        "docs/compiler/ARCHITECTURE.md",
        "docs/compiler/LLVM_BACKEND_PLAN.md",
        "docs/compiler/SELF_HOSTING_PLAN.md",
        "docs/compiler/RUNTIME_INDEPENDENCE_PLAN.md",
        "docs/spm/SONA_PACKAGE_MANAGER_ROADMAP.md",
        "docs/devex/LSP_ROADMAP.md",
        "docs/devex/FORMATTER_ROADMAP.md",
        "docs/devex/DEBUGGER_ROADMAP.md",
        "docs/devex/BENCHMARKING_ROADMAP.md",
    ]
    forbidden_claims = [
        "Sona is now independent from Python",
        "Sona has a native LLVM compiler",
        "Sona now creates standalone binaries",
        "Sona has a completed package registry",
        "Sona has production-ready LSP completion",
        "Sona has production-ready debugger support",
        "Sona has native memory management",
    ]

    for relative in roadmap_docs:
        path = ROOT / relative
        assert path.exists(), relative
        text = path.read_text(encoding="utf-8")
        assert "Sona `0.15.0`" in text
        for claim in forbidden_claims:
            assert claim not in text
