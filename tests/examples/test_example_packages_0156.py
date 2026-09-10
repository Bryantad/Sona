"""Offline sdist -> wheel -> installed-runtime acceptance, outside the checkout."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import sysconfig
import tarfile
import venv
import zipfile
from pathlib import Path

import pytest

from sona.example_catalog import asset_text, find_example, load_manifest

ROOT = Path(__file__).resolve().parents[2]


def _run(arguments, *, cwd, environment=None):
    process = subprocess.run(arguments, cwd=cwd, env=environment, capture_output=True,
                             text=True, encoding="utf-8", errors="replace", timeout=180, check=False)
    assert process.returncode == 0, process.stdout + process.stderr
    return process


@pytest.fixture(scope="module")
def installed_examples(tmp_path_factory):
    workspace = tmp_path_factory.mktemp("example-packages")
    source = workspace / "source"
    source.mkdir()
    for name in ["pyproject.toml", "MANIFEST.in", "setup.py", "README.md", "LICENSE"]:
        shutil.copy2(ROOT / name, source / name)
    for directory in ["sona", "stdlib"]:
        shutil.copytree(ROOT / directory, source / directory,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".sona"))
    manifest = load_manifest()
    assets = {entry["source"] for entry in manifest["examples"]}
    assets.update(asset for entry in manifest["examples"] for asset in entry["assets"])
    for name in assets:
        destination = source / "examples" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / "examples" / name, destination)
    artifacts = workspace / "artifacts"
    _run([sys.executable, "-m", "build", "--sdist", "--no-isolation", "--outdir", str(artifacts)], cwd=source)
    sdist = next(artifacts.glob("*.tar.gz"))
    extracted = workspace / "sdist"
    with tarfile.open(sdist) as archive:
        archive.extractall(extracted, filter="data")
    rebuilt_source = next(extracted.iterdir())
    for name in assets:
        assert (rebuilt_source / "examples" / name).read_text(encoding="utf-8") == asset_text(name)
    _run([sys.executable, "-m", "build", "--wheel", "--no-isolation", "--outdir", str(artifacts)], cwd=rebuilt_source)
    wheel = next(artifacts.glob("*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        assert json.loads(archive.read("sona/data/examples.json")) == manifest
        for name in assets:
            assert archive.read("sona/_examples/" + name).decode("utf-8") == asset_text(name)
    # A real pip installation, no dependency download and no source checkout on PATH.
    environment_root = workspace / "environment"
    venv.EnvBuilder(with_pip=True).create(environment_root)
    python = environment_root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment["PYTHONIOENCODING"] = "utf-8"
    _run([str(python), "-m", "pip", "install", "--no-index", "--no-deps", str(wheel)], cwd=workspace, environment=environment)
    purelib = Path(_run([str(python), "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"],
                        cwd=workspace, environment=environment).stdout.strip())
    # Reuse already-installed test dependencies only. Plain path entries do not
    # evaluate the other environment's editable-install .pth files.
    (purelib / "test-dependencies.pth").write_text(sysconfig.get_path("purelib") + "\n", encoding="utf-8")
    origin = _run([str(python), "-c", "import sona; print(sona.__file__)"], cwd=workspace, environment=environment)
    assert Path(origin.stdout.strip()).is_relative_to(environment_root)
    return python, workspace, environment, purelib, manifest


def test_sdist_rebuilt_wheel_runs_all_python_examples_without_checkout(installed_examples):
    python, workspace, environment, _purelib, manifest = installed_examples
    listed = _run([str(python), "-m", "sona", "examples", "--json"], cwd=workspace, environment=environment)
    assert json.loads(listed.stdout)["examples"] == manifest["examples"]
    for entry in manifest["examples"]:
        if entry["runtime"] != "python":
            continue
        result = _run([str(python), "-m", "sona", "examples", "run", entry["name"], "--json"],
                      cwd=workspace, environment=environment)
        assert json.loads(result.stdout)["status"] == "passed"


def test_installed_native_lessons_verify_real_receipts(installed_examples, native_binary):
    python, workspace, environment, _purelib, _manifest = installed_examples
    environment = {**environment, "SONA_NATIVE_BINARY": str(native_binary)}
    for topic in ("guardian", "proof-mode"):
        result = _run([str(python), "-m", "sona", "learn", "run", topic, "--no-profile", "--json"],
                      cwd=workspace, environment=environment)
        payload = json.loads(result.stdout)
        assert payload["status"] == "passed"
        assert payload["receipt"]["status"] == "valid"
        assert payload["progress_recorded"] is False
    assert not (workspace / ".sona").exists()


def test_every_designated_documentation_block_matches_executed_asset():
    pattern = re.compile(r"<!-- sona-example: ([a-z][a-z0-9-]*) -->\s*```sona\r?\n(.*?)```", re.DOTALL)
    seen = []
    for path in (ROOT / "docs").rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        marked = pattern.findall(text)
        # Reject malformed markers rather than silently omitting their CI duty.
        assert len(marked) == text.count("<!-- sona-example:"), path
        for name, source in marked:
            assert source == asset_text(find_example(name)["source"]), (path, name)
            seen.append(name)
    assert {"conditions", "loops", "collections", "files"}.issubset(seen)


def test_learning_document_local_links_resolve():
    path = ROOT / "docs/guides/learning-and-examples.md"
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
        if "://" not in target and not target.startswith("#"):
            assert (path.parent / target.split("#")[0]).exists(), target
