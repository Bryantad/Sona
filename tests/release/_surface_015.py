from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

STABLE_UTILITY = {
    "path",
    "format",
    "color",
    "assert",
    "uuid",
    "url",
    "csv",
    "pipe",
    "intent",
    "focus",
    "log",
}

STABLE_ACCESSIBILITY = {
    "profile",
    "simplify",
    "breadcrumb",
    "flow",
    "explain",
    "pace",
    "affirm",
    "chunk",
    "timer",
    "noise",
    "tone",
    "readability",
    "linewidth",
    "mirror",
    "chunk_read",
    "contract",
    "boundary",
    "routine",
    "strict",
    "certainty",
    "sensory",
}

EXPERIMENTAL_ACCESSIBILITY = {
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
}

RESILIENCE = {"guardian"}

PUBLIC_015_SURFACES = (
    STABLE_UTILITY | STABLE_ACCESSIBILITY | EXPERIMENTAL_ACCESSIBILITY | RESILIENCE
)

PUBLIC_DOCS = {
    "utility": ROOT / "docs" / "STDLIB_REFERENCE.md",
    "accessibility": ROOT / "docs" / "ACCESSIBILITY_REFERENCE.md",
    "resilience": ROOT / "docs" / "GUARDIAN_REFERENCE.md",
}

