"""Execute shipped examples with the real runtimes in disposable workspaces.

This is not an OS sandbox and does not execute caller-supplied source. Native
Proof Mode production remains solely in Native Core; verification uses proof.py.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from .example_catalog import ExampleError, asset_text, find_example

TIMEOUT_SECONDS = 30
MAX_OUTPUT_BYTES = 64 * 1024


def _environment() -> dict[str, str]:
    environment = os.environ.copy()
    # The installed runtime or this exact checkout, never a cwd-relative import.
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parent.parent)
    environment["PYTHONIOENCODING"] = "utf-8"
    environment["PYTHONUTF8"] = "1"
    return environment


def _execute(arguments: list[str], root: Path, environment: dict[str, str]) -> dict:
    """Bound process time and captured output; never invoke a command shell."""
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        try:
            process = subprocess.Popen(arguments, cwd=root, env=environment,
                                       stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                       shell=False)
        except OSError as exc:
            raise ExampleError("SONA-EXAMPLE-003", "The example runtime could not be started.",
                               "Check the Sona installation and runtime permissions.") from exc
        try:
            deadline = time.monotonic() + TIMEOUT_SECONDS
            while True:
                sizes = [os.fstat(stream.fileno()).st_size for stream in (stdout, stderr)]
                if sum(sizes) > MAX_OUTPUT_BYTES or time.monotonic() > deadline:
                    raise ExampleError("SONA-EXAMPLE-004", "The example exceeded its time or output limit.",
                                       "Review the installation; shipped examples should finish within 30 seconds and 64 KiB.")
                if process.poll() is not None:
                    # Check once more after exit, covering a final output burst.
                    if sum(os.fstat(s.fileno()).st_size for s in (stdout, stderr)) > MAX_OUTPUT_BYTES:
                        raise ExampleError("SONA-EXAMPLE-004", "The example exceeded its output limit.",
                                           "Review the shipped example and Sona installation.")
                    break
                time.sleep(0.02)
            stdout.seek(0)
            stderr.seek(0)
            return {
                "exit_code": process.returncode,
                "stdout": stdout.read(MAX_OUTPUT_BYTES).decode("utf-8", errors="replace").replace("\r\n", "\n"),
                "stderr": stderr.read(MAX_OUTPUT_BYTES).decode("utf-8", errors="replace").replace("\r\n", "\n"),
            }
        finally:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)


def _guardian_command(action: str, root: Path, environment: dict[str, str]) -> dict:
    import json

    result = _execute([sys.executable, "-m", "sona", "guardian", action,
                       "--project-root", str(root), "--format", "json"], root, environment)
    if result["exit_code"] != 0:
        raise ExampleError("SONA-EXAMPLE-005", "The Guardian example setup or state check failed.",
                           "Run the Guardian workflow tests; no learning progress was recorded.")
    try:
        payload = json.loads(result["stdout"])
        if not isinstance(payload, dict):
            raise TypeError("object required")
        return payload
    except (ValueError, TypeError, RecursionError) as exc:
        raise ExampleError("SONA-EXAMPLE-005", "Guardian did not return a structured result.",
                           "Check the Sona runtime installation.") from exc


def _run(entry: dict, root: Path) -> dict:
    from .proof import ProofDiagnostic, verify_receipt

    environment = _environment()
    checks = []

    def check(identifier: str, passed: bool) -> None:
        checks.append({"id": identifier, "passed": bool(passed)})

    source = root / "examples" / entry["source"]
    for asset in dict.fromkeys([entry["source"], *entry["assets"]]):
        target = root / "examples" / asset
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(asset_text(asset), encoding="utf-8", newline="\n")

    receipt_facts = None
    guardian_facts = None
    if entry["runtime"] == "python":
        checked = _execute([sys.executable, "-m", "sona", "check", str(source)], root, environment)
        check("canonical-parser", checked["exit_code"] == 0)
        execution = checked
        if checked["exit_code"] == 0:
            execution = _execute([sys.executable, "-m", "sona", "run", str(source),
                                  "--compatibility", "sona"], root, environment)
        check("execution-succeeded", execution["exit_code"] == 0)
        check("expected-stdout", execution["stdout"] == entry["stdout"])
        check("empty-stderr", execution["stderr"] == "")
        if entry["name"] == "files":
            written = root / "practice.txt"
            check("file-roundtrip", written.is_file() and written.read_text(encoding="utf-8") == "Sona file practice")
    else:
        from .cli import SONA_VERSION, _resolve_native_proof_binary
        from .native_launcher import probe_native_version

        binary = _resolve_native_proof_binary(environment)
        probe_native_version(binary, SONA_VERSION, environment)
        receipt = root / ".sona/receipts/example.sproof"
        receipt.parent.mkdir(parents=True, exist_ok=True)
        arguments = [str(binary), "proof", str(source), "--receipt", str(receipt), "--engine", "native"]
        denied = entry["runtime"] == "guardian-proof"
        if denied:
            initialized = _guardian_command("init", root, environment)
            check("guardian-initialized", initialized.get("status") == "initialized")
            guardian_facts = _guardian_command("check", root, environment)
            explained = _guardian_command("explain", root, environment)
            check("guardian-ready", guardian_facts.get("status") == "ok"
                  and guardian_facts.get("proof_mode", {}).get("ready") is True)
            check("guardian-explained", explained.get("guardian_status") == "ok")
            decisions = guardian_facts.get("capability_decisions", [])
            check("guardian-default-deny", len(decisions) > 0 and all(d.get("decision") == "deny" for d in decisions))
            # A CLI grant must not override this new project's default-deny policy.
            arguments.extend(["--guardian-root", str(root), "--allow-fs-write"])
        execution = _execute(arguments, root, environment)
        check("expected-exit", execution["exit_code"] == (1 if denied else 0))
        check("expected-stdout", execution["stdout"] == entry["stdout"])
        try:
            receipt_facts = verify_receipt(receipt)
        except ProofDiagnostic:
            check("receipt-integrity", False)
        else:
            check("receipt-integrity", receipt_facts["status"] == "valid")
            engine = receipt_facts["engine"]
            check("native-no-python-no-fallback", engine["name"] == "native"
                  and engine["python_required"] is False and engine["python_embedded"] is False
                  and engine["fallback_used"] is False)
            if denied:
                from .stdlib.native_guardian import guardian_proof_verify

                verification = guardian_proof_verify(root, str(receipt))
                check("guardian-binding", receipt_facts["guardian_bound"] is True
                      and verification.get("status") == "verified")
                check("write-denied", receipt_facts["execution"]["status"] == "failed"
                      and (receipt_facts["execution"].get("diagnostic") or {}).get("id") == "SONA-FS-005"
                      and receipt_facts["capabilities"]["filesystem_write"] is False)
                check("denied-effect", any(effect.get("effect") == "FS.WRITE"
                      and effect["outcome"] == "denied" for effect in receipt_facts["effects"]))
                check("no-file-created", not (root / "blocked.txt").exists())
            else:
                check("successful-execution", receipt_facts["execution"]["status"] == "ok")
                check("console-effect", any(effect["scope"] == "console" and effect["outcome"] == "allowed"
                      for effect in receipt_facts["effects"]))
    passed = all(item["passed"] for item in checks)
    return {
        "schema_version": 1, "command": "examples run", "example": entry["name"],
        "status": "passed" if passed else "failed", "runtime": entry["runtime"],
        "checks": checks, "execution": execution, "receipt": receipt_facts,
        "guardian": guardian_facts,
        "workspace": "temporary-removed", "progress_recorded": False,
        "diagnostic": None if passed else ExampleError(
            "SONA-EXAMPLE-005", "An example check failed.",
            "Review the failed checks; no learning progress was recorded.").to_dict(),
    }


def run_example(name: str) -> dict:
    entry = find_example(name)
    try:
        with tempfile.TemporaryDirectory(prefix="sona-example-") as temporary:
            result = _run(entry, Path(temporary))
        return result
    except OSError as exc:
        raise ExampleError("SONA-EXAMPLE-003", "The example workspace or assets could not be used.",
                           "Check temporary-directory permissions and the Sona installation.") from exc
