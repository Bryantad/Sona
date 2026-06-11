import json
import statistics
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run_probe(*args):
    started = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, "-m", "sona", "probe", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    elapsed = time.perf_counter() - started
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return json.loads(proc.stdout), elapsed


def test_stdlib_probe_is_static_and_fast():
    samples = []
    payload = None
    for _ in range(3):
        payload, elapsed = run_probe("stdlib")
        samples.append(elapsed)
    assert payload is not None
    assert payload["mode"] == "static"
    assert payload["status"] == "ok"
    assert payload["errors"] == {}
    assert payload["smod_errors"] == {}
    assert statistics.median(samples) < 5.0


def test_stdlib_probe_filters_and_hides_private_modules():
    payload, _ = run_probe("stdlib", "--category", "utility")
    assert payload["filters"]["category"] == "utility"
    assert "path" in payload["user_modules"]

    payload, _ = run_probe("stdlib", "--stability", "experimental")
    assert payload["filters"]["stability"] == "experimental"
    assert all(
        module["stability_group"] == "experimental"
        for module in payload["modules"]
    )

    payload, _ = run_probe("stdlib")
    assert "native_bridge" not in payload["user_modules"]
    assert "native_intrinsics" not in payload["user_modules"]
    assert "intrinsics" not in payload["user_modules"]
    assert not any(name.startswith("native_") for name in payload["user_modules"])


def test_accessibility_and_guardian_probes_are_static():
    accessibility, _ = run_probe("accessibility")
    assert accessibility["mode"] == "static"
    assert accessibility["status"] == "ok"
    assert "profile" in accessibility["user_modules"]
    assert any(module["name"] == "profile" for module in accessibility["modules"])

    guardian, _ = run_probe("guardian")
    assert guardian["mode"] == "static"
    assert guardian["status"] == "ok"
    assert any(module["name"] == "guardian" for module in guardian["modules"])
