"""Deterministic developer-task summaries shared by every client."""
from __future__ import annotations

import re


def analyze_structure(source: str) -> dict[str, object]:
    lines = source.splitlines()
    names = re.findall(r"\b(?:func|def)\s+(\w+)", source)
    return {
        "code_lines": sum(bool(line.strip()) for line in lines),
        "functions": names,
        "loops": source.count("for ") + source.count("while "),
        "conditionals": source.count("if ") + source.count("elif "),
        "comments": source.count("//") + source.count("#"),
    }


def explain_source(source: str, style: str = "simple") -> str:
    analysis = analyze_structure(source)
    names = analysis["functions"]
    parts = ["This code performs a Sona programming task."]
    if names:
        parts.append(f"It defines function(s): {', '.join(names[:5])}.")
    if "import " in source:
        parts.append("It imports one or more modules before running the main work.")
    if "print(" in source:
        parts.append("It prints output for the user.")
    if "return" in source:
        parts.append("At least one function returns a computed value.")
    if analysis["conditionals"]:
        parts.append("It includes conditional decision logic.")
    if analysis["loops"]:
        parts.append("It includes repeated work through a loop.")
    result = " ".join(parts)
    if style in {"detailed", "cognitive"}:
        result += (
            f"\n\nCode structure:\n- {analysis['code_lines']} non-empty line(s)"
            f"\n- {len(names)} function definition(s)\n- {analysis['loops']} loop(s)"
            f"\n- {analysis['conditionals']} conditional branch(es)\n- {analysis['comments']} comment line marker(s)"
        )
    return result


def suggest_source(source: str) -> str:
    analysis = analyze_structure(source)
    suggestions: list[str] = []
    if analysis["code_lines"] > 25:
        suggestions.append("Break the file into smaller sections or helper functions for easier review.")
    if analysis["comments"] == 0 and analysis["code_lines"] > 8:
        suggestions.append("Add short comments around non-obvious steps to reduce cognitive load.")
    if analysis["loops"]:
        suggestions.append("Review loop bodies for repeated work that could be computed once.")
    if not suggestions:
        suggestions.append("No high-priority local suggestions were found.")
    return "Local suggestions:\n" + "\n".join(f"- {item}" for item in suggestions[:5])
