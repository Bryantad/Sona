"""Thin examples/learning CLI; execution and Guide knowledge stay separate."""

from __future__ import annotations

import argparse
import json


def add_learning_parsers(subparsers) -> None:
    examples = subparsers.add_parser("examples", help="List or run shipped, checked examples")
    examples.add_argument("--json", action="store_true")
    actions = examples.add_subparsers(dest="example_action")
    run = actions.add_parser("run", help="Run one shipped example in a temporary workspace")
    run.add_argument("name")
    run.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    learn = subparsers.add_parser("learn", help="Explore lessons or explicitly practice with the real runtime")
    learn.add_argument("topic", nargs="?", help="Lesson topic, or 'run' to execute practice")
    learn.add_argument("lesson", nargs="?", help="Topic after 'run'")
    learn.add_argument("--json", action="store_true")
    learn.add_argument("--project-root", default=".", help="Existing project for explicit practice progress")
    learn.add_argument("--no-profile", action="store_true", help="Do not read or write learning state")
    learn.add_argument("--mode", choices=("guided", "balanced", "expert"), default=None)


def _render(result: dict) -> str:
    lines = ["Sona Learning" if result["command"].startswith("learn") else "Sona Examples", ""]
    if "examples" in result:
        lines.extend(f"  {entry['name']:<16} {entry['runtime']}" for entry in result["examples"])
        lines.extend(["", "Run: sona examples run <name>",
                      "Python examples do not produce Native evidence. Native examples require matching Native Core."])
    elif "lessons" in result:
        lines.extend(f"  {entry['concept']:<16} {entry['familiarity']} ({entry['runtime']})" for entry in result["lessons"])
        lines.extend(["", "Explore: sona learn <topic>", "Practice: sona learn run <topic>",
                      "Familiarity is local, editable practice state, not a mastery score."])
    elif "checks" in result:
        lines.extend([f"Example        {result['example']}", f"Checks         {result['status'].upper()}",
                      f"Runtime        {result['runtime']}", "Workspace      temporary"])
        for item in result["checks"]:
            lines.append(f"  {'OK' if item['passed'] else 'FAIL'} {item['id']}")
        if result["execution"]["stdout"]:
            lines.extend(["", "Program output", result["execution"]["stdout"].rstrip("\n")])
        if result.get("receipt"):
            facts = result["receipt"]
            lines.extend(["", f"Receipt        {facts['status'].upper()}",
                          f"Execution      {facts['execution']['status'].upper()}",
                          "Receipt validity is self-consistency, not producer authentication or remote attestation."])
        if result["command"].startswith("learn"):
            lines.append("Progress       " + ("recorded locally" if result["progress_recorded"] else "not recorded"))
    elif "lesson" in result:
        lines.extend([result["lesson"]["explanation"]["text"], "", result["lesson"]["practice_command"],
                      result["lesson"]["progress_rule"]])
    if result.get("diagnostic"):
        diagnostic = result["diagnostic"]
        lines.extend([f"{diagnostic['diagnostic_id']}: {diagnostic['message']}", f"  hint: {diagnostic['hint']}"])
    return "\n".join(lines)


def handle_learning_command(args) -> int:
    from .cli import safe_print
    from .example_catalog import ExampleError, load_manifest
    from .example_runner import run_example
    from .guide.learning import lesson, lessons, record_practice
    from .guide.models import GuideError
    from .guide.profile import default_profile, load_profile_state
    from .native_launcher import NativeProofLaunchError

    result = None
    try:
        if args.command == "examples":
            if args.example_action == "run":
                result = run_example(args.name)
            else:
                manifest = load_manifest()
                result = {"schema_version": 1, "command": "examples", "status": "ok",
                          "manifest_revision": manifest["revision"], "examples": manifest["examples"]}
        else:
            profile = default_profile() if args.no_profile else load_profile_state(args.project_root).profile
            if args.topic == "run":
                selected = lesson(args.lesson, profile, mode=args.mode)
                result = run_example(selected["example"])
                result["command"] = "learn run"
                result["concept"] = selected["concept"]
                if result["status"] == "passed" and not args.no_profile:
                    result["profile"] = record_practice(args.project_root, selected["concept"])
                    result["progress_recorded"] = True
            elif args.lesson is not None:
                raise ExampleError("SONA-EXAMPLE-001", "Unexpected lesson argument.", "Use `sona learn <topic>` or `sona learn run <topic>`.")
            elif args.topic is None:
                result = {"schema_version": 1, "command": "learn", "status": "ok", "lessons": lessons(profile)}
            else:
                result = {"schema_version": 1, "command": "learn", "status": "ok",
                          "lesson": lesson(args.topic, profile, mode=args.mode)}
    except (ExampleError, GuideError, NativeProofLaunchError) as exc:
        diagnostic = {"diagnostic_id": exc.diagnostic_id, "message": exc.message, "hint": exc.hint}
        # Preserve passed execution checks if only the explicit profile write failed.
        result = {**(result or {}), "schema_version": 1, "command": args.command,
                  "status": "unavailable", "diagnostic": diagnostic, "progress_recorded": False}
    safe_print(json.dumps(result, sort_keys=True) if args.json else _render(result))
    return 0 if result["status"] in {"ok", "passed"} else 1
