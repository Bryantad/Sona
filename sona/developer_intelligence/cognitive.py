"""Deterministic syntax-aware cognitive diagnostics shared by CLI and LSP."""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import fields, is_dataclass
from typing import Any

from .diagnostics import Diagnostic, SourceSpan, diagnostic


PROFILE_LIMITS = {
    "standard": {"function_lines": 60, "branching": 8, "block_lines": 30, "nesting": 5, "concepts": 45, "repeats": 3, "hints": 8},
    "adhd": {"function_lines": 40, "branching": 6, "block_lines": 20, "nesting": 4, "concepts": 30, "repeats": 3, "hints": 4},
    "dyslexia": {"function_lines": 50, "branching": 7, "block_lines": 24, "nesting": 4, "concepts": 35, "repeats": 3, "hints": 5},
    "autism": {"function_lines": 55, "branching": 7, "block_lines": 26, "nesting": 5, "concepts": 40, "repeats": 4, "hints": 6},
    "low-stimulation": {"function_lines": 45, "branching": 6, "block_lines": 22, "nesting": 4, "concepts": 30, "repeats": 3, "hints": 4},
}


def _syntax_metrics(source: str) -> tuple[int, int, Counter[str]]:
    """Return (control-node count, maximum AST depth, subtree signatures)."""
    try:
        from sona.parser_v090 import SonaParserv090
        nodes = SonaParserv090().parse(source) or []
    except Exception:
        return 0, 0, Counter()
    control = 0
    maximum_depth = 0
    signatures: Counter[str] = Counter()
    seen: set[int] = set()

    def walk(value: Any, depth: int = 0) -> None:
        nonlocal control, maximum_depth
        if value is None or isinstance(value, (str, bytes, int, float, bool)):
            return
        if isinstance(value, dict):
            for item in value.values():
                walk(item, depth)
            return
        if isinstance(value, (list, tuple, set)):
            for item in value:
                walk(item, depth)
            return
        identity = id(value)
        if identity in seen:
            return
        seen.add(identity)
        name = type(value).__name__
        is_control = any(token in name for token in ("If", "While", "For", "Repeat", "Function", "Match"))
        child_depth = depth + 1 if is_control else depth
        if is_control:
            control += 1
            maximum_depth = max(maximum_depth, child_depth)
        child_names: list[str] = []
        if is_dataclass(value):
            for item in fields(value):
                if item.name in {"span", "line_number"}:
                    continue
                child = getattr(value, item.name, None)
                if not isinstance(child, (str, bytes, int, float, bool, type(None))):
                    child_names.append(type(child).__name__)
                walk(child, child_depth)
        elif hasattr(value, "__dict__"):
            for key, child in vars(value).items():
                if key in {"span", "line_number"} or key.startswith("_"):
                    continue
                walk(child, child_depth)
        if name.endswith(("Expression", "Statement")):
            signatures[f"{name}:{','.join(child_names)}"] += 1

    walk(nodes)
    return control, maximum_depth, signatures


def _block_metrics(lines: list[str]) -> tuple[int, list[tuple[int, int]]]:
    stack: list[int] = []
    maximum = 0
    blocks: list[tuple[int, int]] = []
    for number, line in enumerate(lines, start=1):
        for character in line:
            if character == "{":
                stack.append(number)
                maximum = max(maximum, len(stack))
            elif character == "}" and stack:
                start = stack.pop()
                blocks.append((start, number - start + 1))
    return maximum, blocks


def analyze_source(source: str, *, file: str = "<string>", profile: str = "standard") -> tuple[Diagnostic, ...]:
    limits = PROFILE_LIMITS.get(profile, PROFILE_LIMITS["standard"])
    lines = source.splitlines()
    findings: list[Diagnostic] = []
    ast_branches, ast_depth, signatures = _syntax_metrics(source)
    lexical_branches = sum(len(re.findall(r"\b(if|else|when|for|while)\b", line)) for line in lines)
    branches = max(ast_branches, lexical_branches)
    brace_depth, blocks = _block_metrics(lines)
    nesting = max(ast_depth, brace_depth)
    if nesting > limits["nesting"]:
        findings.append(diagnostic("SONA-COG-001", "cognitive", f"Deep nesting ({nesting} levels).", severity="warning", hint="Extract a named helper or use an early return.", span=SourceSpan(file=file), source="cognitive"))
    if branches > limits["branching"]:
        findings.append(diagnostic("SONA-COG-003", "cognitive", f"High branching density ({branches} branches).", severity="warning", hint="Extract named decisions or smaller helper functions.", span=SourceSpan(file=file), source="cognitive"))

    function_starts: list[int] = []
    for number, line in enumerate(lines, start=1):
        if re.search(r"\b(?:func|def)\s+\w+", line):
            function_starts.append(number)
    function_sizes = [
        size for start, size in blocks if start in function_starts
    ]
    if function_sizes and max(function_sizes) > limits["function_lines"]:
        findings.append(diagnostic("SONA-COG-002", "cognitive", f"Large function ({max(function_sizes)} lines).", severity="warning", hint="Split the work into smaller named functions.", span=SourceSpan(file=file), source="cognitive"))

    repeated = sum(1 for count in signatures.values() if count >= limits["repeats"])
    normalized_lines = Counter(re.sub(r"\b\d+\b", "#", line.strip()) for line in lines if len(line.strip()) >= 12)
    repeated += sum(1 for count in normalized_lines.values() if count >= limits["repeats"])
    if repeated:
        findings.append(diagnostic("SONA-COG-004", "cognitive", "Repeated code structure detected.", severity="info", hint="Consider extracting the repeated structure into a helper.", span=SourceSpan(file=file), source="cognitive"))

    long_blocks = [(start, size) for start, size in blocks if size > limits["block_lines"]]
    if long_blocks:
        start, size = max(long_blocks, key=lambda item: item[1])
        findings.append(diagnostic("SONA-COG-007", "cognitive", f"Long block ({size} lines).", severity="warning", hint="Add a named boundary within this block.", span=SourceSpan(file=file, start_line=start, start_column=1), source="cognitive"))

    identifiers = set(re.findall(r"\b[A-Za-z_]\w*\b", source)) - {"let", "const", "func", "if", "else", "for", "while", "return", "true", "false", "nil"}
    if len(identifiers) > limits["concepts"]:
        findings.append(diagnostic("SONA-COG-008", "cognitive", f"High concept load ({len(identifiers)} distinct names).", severity="info", hint="Group related concepts behind a smaller interface.", span=SourceSpan(file=file), source="cognitive"))

    for number, line in enumerate(lines, start=1):
        if len(re.findall(r"[+*/%<>=&|!-]", line)) > 12:
            findings.append(diagnostic("SONA-COG-005", "cognitive", "Dense expression may obscure intent.", severity="warning", hint="Name intermediate values.", span=SourceSpan(file=file, start_line=number, start_column=1, end_line=number, end_column=len(line) + 1), source="cognitive"))
        names = re.findall(r"\b(?:let|const)\s+([A-Za-z_]\w*)", line)
        if any(len(name) == 1 and name not in {"i", "j", "k"} for name in names):
            findings.append(diagnostic("SONA-COG-006", "cognitive", "A one-character name may be unclear.", severity="info", hint="Use a short descriptive name.", span=SourceSpan(file=file, start_line=number, start_column=1), source="cognitive"))
    return tuple(findings[: limits["hints"]])
