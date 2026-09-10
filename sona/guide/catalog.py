"""Reviewed explanations of existing diagnostics, with executable examples."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

CATALOG_VERSION = 1


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    topic: str
    summary: str
    simple: str
    technical: str
    visual: str
    next_step: str
    example: str
    example_kind: str
    concepts: tuple[str, ...]


_NAME = CatalogEntry(
    topic="names",
    summary="A name is not defined where it is being used.",
    simple="A variable gives a value a name. Check that you declared the name "
    "and spelled it the same way when using it.",
    technical="Name lookup could not resolve a binding in the visible runtime scope.",
    visual="declaration: quantity = 3\n                  |\nuse: price * quantity",
    next_step="Check the spelling and visible declarations. Only rename a use when "
    "you have confirmed which binding it should refer to.",
    example="let price = 10;\nlet quantity = 3;\nlet total = price * quantity;\nprint(total);",
    example_kind="sona",
    concepts=("variables", "scope"),
)
_DELIMITER = CatalogEntry(
    topic="delimiters",
    summary="Sona could not parse the source and detected an unclosed delimiter.",
    simple="Parentheses, square brackets, and braces come in pairs. A missing closing "
    "character can make the rest of the file hard to read.",
    technical="The canonical parser failed and its delimiter scan detected an unmatched "
    "opening delimiter. The reported position need not identify the missing closer.",
    visual="( expression )\n[ item, item ]\n{ statements }",
    next_step="Inspect the reported location and the opening delimiters before it. "
    "Check again after repairing the pair; other syntax errors may remain.",
    example="let total = (2 + 3);\nprint(total);",
    example_kind="sona",
    concepts=("delimiters",),
)
_FILESYSTEM = CatalogEntry(
    topic="filesystem-permission",
    summary="A filesystem operation was denied by the capability controls.",
    simple="The operation needs permission to read or write files. The actual "
    "diagnostic tells you which operation was denied.",
    technical="The filesystem capability check rejected the requested operation. "
    "Native Core checks explicit read/write capabilities, including Guardian policy "
    "when a Guardian root is supplied.",
    visual="filesystem request -> capability check -> denied\n                                     |\n                             review required access",
    next_step="Review the requested access first. Native reads use --allow-fs-read; "
    "writes use --allow-fs-write. With --guardian-root, also review the project's "
    "policy using sona guardian explain. A CLI flag does not override a policy denial.",
    example="sona-native run app.sona --engine native --allow-fs-read",
    example_kind="command",
    concepts=("native-capabilities", "guardian", "proof-mode"),
)
_INTEGRITY = CatalogEntry(
    topic="receipt-integrity",
    summary="The Proof Mode receipt hash does not match its canonical contents.",
    simple="The receipt's contents and its recorded hash disagree. Use the original "
    "receipt or create a new one from a reviewed program.",
    technical="The shared verifier's SHA-256 of the canonical unsigned schema-1 "
    "payload differs from receipt_hash. Self-consistency does not authenticate "
    "the producer or prevent someone replacing and re-hashing a receipt.",
    visual="canonical receipt contents -> recomputed hash\n                                      !=\n                                recorded hash",
    next_step="Preserve the failed receipt for investigation. Retrieve an intact "
    "original or generate new evidence, then use sona proof verify. Do not repair "
    "the receipt by replacing its hash.",
    example="sona proof verify receipt.sproof",
    example_kind="command",
    concepts=("proof-mode", "receipt-integrity"),
)
_GUARDIAN_ROOT = CatalogEntry(
    topic="guardian-readiness",
    summary="Guardian could not use the selected project root.",
    simple="Guardian needs an existing project directory it can access.",
    technical="Guardian project-root resolution failed before a usable local "
    "policy and baseline could be established.",
    visual="project directory -> Guardian configuration -> trusted baseline",
    next_step="Select your real project directory, then run sona guardian check "
    "--project-root . there. Initialize only the intended project if it is new.",
    example="sona guardian check --project-root .",
    example_kind="command",
    concepts=("guardian", "project-boundaries"),
)
_GUARDIAN_CONFIG = CatalogEntry(
    topic="guardian-readiness",
    summary="Guardian configuration could not be validated.",
    simple="Guardian could not read or accept part of the project's settings.",
    technical="The configuration may be unreadable, malformed, use an unsupported "
    "schema, or contain an unsupported capability or decision.",
    visual="sona.guard.json -> read -> validate -> policy identity",
    next_step="Review the diagnostic reason and sona.guard.json. Run sona guardian "
    "check after correcting the configuration. Review drift before trusting a changed policy.",
    example="sona guardian explain --project-root .",
    example_kind="command",
    concepts=("guardian", "native-capabilities"),
)
_GUARDIAN_STATE = CatalogEntry(
    topic="guardian-readiness",
    summary="Guardian trusted state is incomplete or inconsistent.",
    simple="Guardian could not establish a consistent saved baseline and policy.",
    technical="Trusted-state validation failed. This can include partial "
    "initialization, unreadable state, or a mismatched canonical policy identity.",
    visual="saved policy + saved baseline -> consistency check",
    next_step="Run sona guardian check and review .sona/guardian. Preserve existing "
    "state before repair; do not silently replace a baseline to dismiss a failure.",
    example="sona guardian check --project-root .",
    example_kind="command",
    concepts=("guardian", "baselines", "proof-mode"),
)

CATALOG = MappingProxyType({
    "SONA-RUNTIME-003": _NAME,
    "SONA-NATIVE-RUNTIME-003": _NAME,
    "SONA-PARSE-003": _DELIMITER,
    "SONA-FS-005": _FILESYSTEM,
    "PROOF-VERIFY-005": _INTEGRITY,
    "SONA-GUARD-001": _GUARDIAN_ROOT,
    "SONA-GUARD-002": _GUARDIAN_CONFIG,
    "SONA-GUARD-004": _GUARDIAN_STATE,
})


@dataclass(frozen=True, slots=True)
class ConceptEntry:
    title: str
    summary: str
    simple: str
    technical: str
    visual: str
    example: str


CONCEPTS = MappingProxyType({
    "variables": ConceptEntry(
        "Variables", "A binding associates a name with a value.",
        "Declare a name before using it, and use the same spelling.",
        "Name lookup resolves a binding in the visible scope; declaration and assignment are distinct operations.",
        "name -> value -> later use", "let quantity = 3;\nprint(quantity);",
    ),
    "conditions": ConceptEntry(
        "Conditions", "A condition selects which branch runs.",
        "An if branch runs when its condition is true; else provides the alternative.",
        "The runtime evaluates branch conditions and executes the selected statement body.",
        "condition -> true: if body\n          -> false: else body",
        'if true { print("yes"); } else { print("no"); }',
    ),
    "loops": ConceptEntry(
        "Loops", "A loop repeats a statement body.",
        "For visits items in a collection. While repeats while its condition remains true.",
        "Iteration evaluates the iterable or condition using the runtime's loop and execution limits.",
        "next item / condition -> body -> next iteration",
        "for value in [1, 2, 3] { print(value); }",
    ),
    "functions": ConceptEntry(
        "Functions", "A function gives a reusable body a name and parameters.",
        "Arguments supply values for the parameters. Return supplies the result.",
        "A call binds arguments in a function scope and evaluates its body under runtime call limits.",
        "arguments -> parameters -> body -> return value",
        "func twice(value) { return value * 2; }\nprint(twice(3));",
    ),
    "collections": ConceptEntry(
        "Collections", "Lists and maps group values.",
        "Lists keep values in order. Maps associate keys with values.",
        "List and dictionary expressions construct collections; indexing uses the runtime's key/index rules.",
        "list: index -> value\nmap: key -> value", "let values = [1, 2, 3];\nprint(values[0]);",
    ),
    "modules": ConceptEntry(
        "Modules", "An import makes a module available to the program.",
        "Use an imported module's public names through its binding.",
        "The runtime resolves imports and exposes the module's public interface. Static explanation does not import or execute it.",
        "import -> module binding -> public member", "import math;\nprint(math.sqrt(9));",
    ),
    "files": ConceptEntry(
        "Files", "File operations use explicit filesystem APIs.",
        "Use fs.read_text and fs.write_text. Review the access needed before running the program.",
        "Native Core checks filesystem capabilities; a Guardian policy denial is not overridden by a CLI grant.",
        "file request -> capability decision -> operation / denial", "import fs;",
    ),
    "guardian": ConceptEntry(
        "Guardian", "Guardian manages project-local policy and baseline state.",
        "Check and explain the selected project's state before using it for execution.",
        "Policy and baseline checks describe local consistency and capability decisions; they do not authenticate a host or producer.",
        "policy -> capability decision -> execution -> Proof Mode receipt", "import guardian;",
    ),
    "proof-mode": ConceptEntry(
        "Proof Mode", "Proof Mode records observed Native execution evidence.",
        "Inspect and verify a receipt to understand its recorded result and integrity.",
        "Schema-1 self-hashing establishes receipt self-consistency, not producer authentication, signatures, or remote attestation.",
        "Native execution -> receipt -> shared verifier -> inspection",
        "sona proof inspect receipt.sproof",
    ),
})

SYNTAX_CONCEPTS = MappingProxyType({
    "var_assignment": "variables", "variable": "variables",
    "enhanced_if_stmt": "conditions", "enhanced_for_stmt": "loops",
    "enhanced_while_stmt": "loops", "func_def": "functions", "return_stmt": "functions",
    "list_literal": "collections", "dict_literal": "collections",
    "import_stmt": "modules", "import_from_stmt": "modules",
})

KEYWORD_CONCEPTS = MappingProxyType({
    "let": "variables", "const": "variables", "if": "conditions", "else": "conditions",
    "for": "loops", "while": "loops", "break": "loops", "continue": "loops",
    "func": "functions", "return": "functions", "import": "modules",
})
