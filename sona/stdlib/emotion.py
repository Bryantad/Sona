"""Emotion detection backend for the Sona emotion module.

Rule-based default implementation.  Each ``detect_from_*`` function
returns a dict of the form::

    {"state": str, "confidence": float, "source": str, "intensity": str}

A pluggable backend registry allows future ML/API-backed detectors to
be swapped in without changing the ``.smod`` surface.
"""

from __future__ import annotations

import math
from typing import Any

# ── Canonical constants ──────────────────────────────────────────

EMOTION_STATES: tuple[str, ...] = (
    "neutral",
    "frustration",
    "curiosity",
    "satisfaction",
    "confusion",
    "fatigue",
)

EMOTION_SOURCES: tuple[str, ...] = (
    "runtime",
    "text",
    "structure",
    "api",
    "composite",
)

INTENSITY_THRESHOLDS: list[tuple[float, str]] = [
    (0.0, "minimal"),
    (0.2, "low"),
    (0.4, "moderate"),
    (0.6, "high"),
    (0.8, "critical"),
]

STRATEGY_MAP: dict[str, dict[str, str]] = {
    "neutral": {
        "strategy": "continue",
        "description": "No intervention required.",
    },
    "frustration": {
        "strategy": "simplify",
        "description": "Reduce complexity; offer concrete next-step guidance.",
    },
    "curiosity": {
        "strategy": "expand",
        "description": "Provide additional context and exploratory paths.",
    },
    "satisfaction": {
        "strategy": "reinforce",
        "description": "Acknowledge positive outcome; suggest refinements.",
    },
    "confusion": {
        "strategy": "clarify",
        "description": "Restate context; surface relevant definitions.",
    },
    "fatigue": {
        "strategy": "pause",
        "description": "Recommend a break or summarise progress so far.",
    },
}


# ── Intensity helper ─────────────────────────────────────────────

def intensity_label(confidence: float) -> str:
    """Map a confidence value (0.0–1.0) to an intensity label."""
    label = "minimal"
    for threshold, name in INTENSITY_THRESHOLDS:
        if confidence >= threshold:
            label = name
    return label


# ── Detection functions ──────────────────────────────────────────

def detect_from_runtime(
    exit_code: int = 0,
    duration_ms: int = 0,
    error_count: int = 0,
) -> dict[str, Any]:
    """Infer emotion state from runtime execution signals."""
    if error_count > 0 or exit_code != 0:
        confidence = min(1.0, 0.5 + error_count * 0.1)
        state = "frustration"
    elif duration_ms > 10_000:
        confidence = min(1.0, 0.3 + (duration_ms - 10_000) / 50_000)
        state = "fatigue"
    elif duration_ms > 5_000:
        confidence = 0.25
        state = "neutral"
    else:
        confidence = 0.1
        state = "satisfaction" if exit_code == 0 and error_count == 0 else "neutral"

    return {
        "state": state,
        "confidence": round(confidence, 4),
        "source": "runtime",
        "intensity": intensity_label(confidence),
    }


_FRUSTRATION_KEYWORDS = {
    "error", "fail", "failed", "failure", "exception", "crash",
    "bug", "broken", "wrong", "stuck",
}
_CURIOSITY_KEYWORDS = {
    "why", "how", "what", "explore", "understand", "learn",
    "interesting", "curious",
}
_CONFUSION_KEYWORDS = {
    "confused", "unclear", "unexpected", "weird", "strange",
    "doesn't make sense", "don't understand",
}
_SATISFACTION_KEYWORDS = {
    "works", "success", "great", "done", "fixed", "resolved",
    "correct", "passed",
}


def detect_from_text(text: str = "") -> dict[str, Any]:
    """Infer emotion state from output/log text via keyword matching."""
    if not text:
        return {
            "state": "neutral",
            "confidence": 0.1,
            "source": "text",
            "intensity": "minimal",
        }

    lower = text.lower()
    words = set(lower.split())

    scores: dict[str, float] = {
        "frustration": len(words & _FRUSTRATION_KEYWORDS) * 0.15,
        "curiosity": len(words & _CURIOSITY_KEYWORDS) * 0.12,
        "confusion": len(words & _CONFUSION_KEYWORDS) * 0.15,
        "satisfaction": len(words & _SATISFACTION_KEYWORDS) * 0.12,
    }
    # Check multi-word phrases
    for phrase in _CONFUSION_KEYWORDS:
        if " " in phrase and phrase in lower:
            scores["confusion"] += 0.15

    best_state = max(scores, key=lambda k: scores[k])
    best_score = scores[best_state]

    if best_score < 0.1:
        return {
            "state": "neutral",
            "confidence": 0.1,
            "source": "text",
            "intensity": "minimal",
        }

    confidence = min(1.0, round(best_score, 4))
    return {
        "state": best_state,
        "confidence": confidence,
        "source": "text",
        "intensity": intensity_label(confidence),
    }


def detect_from_structure(events: list[dict] | None = None) -> dict[str, Any]:
    """Infer emotion state from event-list patterns."""
    if not events:
        return {
            "state": "neutral",
            "confidence": 0.1,
            "source": "structure",
            "intensity": "minimal",
        }

    error_events = [e for e in events if e.get("kind") in ("error", "exception")]
    retry_events = [e for e in events if e.get("kind") == "retry"]

    if len(error_events) >= 3:
        confidence = min(1.0, 0.5 + len(error_events) * 0.08)
        return {
            "state": "frustration",
            "confidence": round(confidence, 4),
            "source": "structure",
            "intensity": intensity_label(confidence),
        }

    if len(retry_events) >= 2:
        confidence = min(1.0, 0.3 + len(retry_events) * 0.1)
        return {
            "state": "confusion",
            "confidence": round(confidence, 4),
            "source": "structure",
            "intensity": intensity_label(confidence),
        }

    return {
        "state": "neutral",
        "confidence": 0.1,
        "source": "structure",
        "intensity": "minimal",
    }


# ── Composite resolution ────────────────────────────────────────

def resolve_composite(detections: list[dict[str, Any]]) -> dict[str, Any]:
    """Resolve multiple detections into a single composite state.

    Uses confidence-weighted voting.  The state with the highest
    cumulative confidence wins.  The composite confidence is the
    weighted mean of all contributing confidences.
    """
    if not detections:
        return {
            "state": "neutral",
            "confidence": 0.0,
            "source": "composite",
            "intensity": "minimal",
        }

    if len(detections) == 1:
        d = detections[0]
        return {
            "state": d["state"],
            "confidence": d["confidence"],
            "source": "composite",
            "intensity": intensity_label(d["confidence"]),
        }

    # Accumulate confidence per state
    state_weights: dict[str, float] = {}
    for d in detections:
        st = d.get("state", "neutral")
        conf = float(d.get("confidence", 0.0))
        state_weights[st] = state_weights.get(st, 0.0) + conf

    best_state = max(state_weights, key=lambda k: state_weights[k])

    # Weighted mean of all confidences
    total_conf = math.fsum(d.get("confidence", 0.0) for d in detections)
    mean_conf = round(total_conf / len(detections), 4)
    mean_conf = min(1.0, mean_conf)

    return {
        "state": best_state,
        "confidence": mean_conf,
        "source": "composite",
        "intensity": intensity_label(mean_conf),
    }


# ── Validation helpers ───────────────────────────────────────────

def is_valid_state(state: str) -> bool:
    """Return *True* if *state* is a recognised emotion state."""
    return state in EMOTION_STATES


def map_strategy(state: str) -> dict[str, str]:
    """Return the response strategy dict for *state*."""
    return dict(STRATEGY_MAP.get(state, STRATEGY_MAP["neutral"]))
