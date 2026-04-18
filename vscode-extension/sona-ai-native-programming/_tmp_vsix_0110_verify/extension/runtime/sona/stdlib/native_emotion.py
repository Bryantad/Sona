"""Native glue exposing :mod:`sona.stdlib.emotion` helpers to Sona.

Each public function follows the ``emotion_<name>`` prefix convention
expected by :class:`~sona.stdlib.native_bridge.NativeBridge`.
"""

from __future__ import annotations

from typing import Any

from . import emotion as _emotion

# ── Constants (exposed as emotion_<NAME>) ────────────────────────

emotion_NEUTRAL = "neutral"
emotion_FRUSTRATION = "frustration"
emotion_CURIOSITY = "curiosity"
emotion_SATISFACTION = "satisfaction"
emotion_CONFUSION = "confusion"
emotion_FATIGUE = "fatigue"

emotion_STATES = list(_emotion.EMOTION_STATES)
emotion_SOURCES = list(_emotion.EMOTION_SOURCES)

# Intensity labels as a list for Sona consumption
emotion_INTENSITY_LABELS = ["minimal", "low", "moderate", "high", "critical"]


# ── Detection bridges ───────────────────────────────────────────

def emotion_detect_runtime(
    exit_code: Any = 0,
    duration_ms: Any = 0,
    error_count: Any = 0,
) -> dict:
    """Bridge to :func:`emotion.detect_from_runtime`."""
    return _emotion.detect_from_runtime(
        exit_code=int(exit_code),
        duration_ms=int(duration_ms),
        error_count=int(error_count),
    )


def emotion_detect_text(text: Any = "") -> dict:
    """Bridge to :func:`emotion.detect_from_text`."""
    return _emotion.detect_from_text(text=str(text) if text else "")


def emotion_detect_structure(events: Any = None) -> dict:
    """Bridge to :func:`emotion.detect_from_structure`."""
    ev = list(events) if events is not None else None
    return _emotion.detect_from_structure(events=ev)


def emotion_resolve_composite(detections: Any) -> dict:
    """Bridge to :func:`emotion.resolve_composite`."""
    return _emotion.resolve_composite(list(detections) if detections else [])


def emotion_intensity_label(confidence: Any) -> str:
    """Bridge to :func:`emotion.intensity_label`."""
    return _emotion.intensity_label(float(confidence))


def emotion_is_valid_state(state: Any) -> bool:
    """Bridge to :func:`emotion.is_valid_state`."""
    return _emotion.is_valid_state(str(state))


def emotion_map_strategy(state: Any) -> dict:
    """Bridge to :func:`emotion.map_strategy`."""
    return _emotion.map_strategy(str(state))


__all__ = [
    "emotion_NEUTRAL",
    "emotion_FRUSTRATION",
    "emotion_CURIOSITY",
    "emotion_SATISFACTION",
    "emotion_CONFUSION",
    "emotion_FATIGUE",
    "emotion_STATES",
    "emotion_SOURCES",
    "emotion_INTENSITY_LABELS",
    "emotion_detect_runtime",
    "emotion_detect_text",
    "emotion_detect_structure",
    "emotion_resolve_composite",
    "emotion_intensity_label",
    "emotion_is_valid_state",
    "emotion_map_strategy",
]
