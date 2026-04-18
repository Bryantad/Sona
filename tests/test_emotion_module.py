"""Tests for the Sona emotion module (emotion.py + native_emotion.py).

Covers detection backends, composite resolution, validation helpers,
intensity mapping, and strategy matrix.
"""

import pytest

from sona.stdlib.emotion import (
    EMOTION_STATES,
    EMOTION_SOURCES,
    INTENSITY_THRESHOLDS,
    STRATEGY_MAP,
    detect_from_runtime,
    detect_from_text,
    detect_from_structure,
    intensity_label,
    is_valid_state,
    map_strategy,
    resolve_composite,
)
from sona.stdlib import native_emotion


# ======================================================================
# Detection — runtime
# ======================================================================


class TestDetectFromRuntime:
    def test_success_path(self):
        result = detect_from_runtime(exit_code=0, duration_ms=50, error_count=0)
        assert result["state"] == "satisfaction"
        assert result["source"] == "runtime"
        assert 0.0 <= result["confidence"] <= 1.0

    def test_failure_path(self):
        result = detect_from_runtime(exit_code=1, duration_ms=50, error_count=0)
        assert result["state"] == "frustration"
        assert result["confidence"] >= 0.5

    def test_errors_raise_confidence(self):
        r1 = detect_from_runtime(exit_code=1, error_count=1)
        r2 = detect_from_runtime(exit_code=1, error_count=5)
        assert r2["confidence"] >= r1["confidence"]

    def test_long_duration_fatigue(self):
        result = detect_from_runtime(exit_code=0, duration_ms=30_000, error_count=0)
        assert result["state"] == "fatigue"


# ======================================================================
# Detection — text
# ======================================================================


class TestDetectFromText:
    def test_empty_text(self):
        result = detect_from_text("")
        assert result["state"] == "neutral"
        assert result["source"] == "text"

    def test_frustration_keywords(self):
        result = detect_from_text("error fail crash")
        assert result["state"] == "frustration"

    def test_satisfaction_keywords(self):
        result = detect_from_text("works great success done")
        assert result["state"] == "satisfaction"

    def test_curiosity_keywords(self):
        result = detect_from_text("why how explore understand")
        assert result["state"] == "curiosity"


# ======================================================================
# Detection — structure
# ======================================================================


class TestDetectFromStructure:
    def test_empty_events(self):
        result = detect_from_structure(None)
        assert result["state"] == "neutral"

    def test_many_errors(self):
        events = [{"kind": "error"} for _ in range(5)]
        result = detect_from_structure(events)
        assert result["state"] == "frustration"

    def test_retries(self):
        events = [{"kind": "retry"} for _ in range(3)]
        result = detect_from_structure(events)
        assert result["state"] == "confusion"


# ======================================================================
# Composite resolution
# ======================================================================


class TestResolveComposite:
    def test_empty(self):
        result = resolve_composite([])
        assert result["state"] == "neutral"
        assert result["source"] == "composite"

    def test_single(self):
        d = {"state": "curiosity", "confidence": 0.7, "source": "text"}
        result = resolve_composite([d])
        assert result["state"] == "curiosity"
        assert result["source"] == "composite"

    def test_multiple_highest_wins(self):
        detections = [
            {"state": "curiosity", "confidence": 0.3, "source": "text"},
            {"state": "frustration", "confidence": 0.8, "source": "runtime"},
        ]
        result = resolve_composite(detections)
        assert result["state"] == "frustration"

    def test_same_state_accumulates(self):
        detections = [
            {"state": "frustration", "confidence": 0.4, "source": "text"},
            {"state": "frustration", "confidence": 0.3, "source": "runtime"},
            {"state": "curiosity", "confidence": 0.5, "source": "structure"},
        ]
        result = resolve_composite(detections)
        # frustration total = 0.7, curiosity total = 0.5
        assert result["state"] == "frustration"


# ======================================================================
# Intensity labels
# ======================================================================


class TestIntensityLabel:
    @pytest.mark.parametrize(
        "confidence,expected",
        [
            (0.0, "minimal"),
            (0.1, "minimal"),
            (0.2, "low"),
            (0.4, "moderate"),
            (0.6, "high"),
            (0.8, "critical"),
            (1.0, "critical"),
        ],
    )
    def test_thresholds(self, confidence, expected):
        assert intensity_label(confidence) == expected


# ======================================================================
# Validation
# ======================================================================


class TestValidation:
    def test_valid_states(self):
        for state in EMOTION_STATES:
            assert is_valid_state(state) is True

    def test_invalid_state(self):
        assert is_valid_state("joy") is False
        assert is_valid_state("") is False

    def test_strategy_map_coverage(self):
        for state in EMOTION_STATES:
            strat = map_strategy(state)
            assert "strategy" in strat
            assert "description" in strat

    def test_unknown_state_falls_back(self):
        strat = map_strategy("nonexistent")
        assert strat == STRATEGY_MAP["neutral"]


# ======================================================================
# Native bridge
# ======================================================================


class TestNativeBridge:
    def test_module_loads(self):
        assert callable(native_emotion.emotion_detect_runtime)
        assert callable(native_emotion.emotion_detect_text)
        assert callable(native_emotion.emotion_detect_structure)
        assert callable(native_emotion.emotion_resolve_composite)
        assert callable(native_emotion.emotion_intensity_label)
        assert callable(native_emotion.emotion_is_valid_state)
        assert callable(native_emotion.emotion_map_strategy)

    def test_constants_exposed(self):
        assert native_emotion.emotion_NEUTRAL == "neutral"
        assert native_emotion.emotion_FRUSTRATION == "frustration"
        assert len(native_emotion.emotion_STATES) == 6
        assert len(native_emotion.emotion_SOURCES) == 5

    def test_bridge_detect_runtime(self):
        result = native_emotion.emotion_detect_runtime(0, 100, 0)
        assert result["state"] in EMOTION_STATES

    def test_bridge_resolve_composite(self):
        detections = [
            {"state": "neutral", "confidence": 0.5, "source": "runtime"},
        ]
        result = native_emotion.emotion_resolve_composite(detections)
        assert result["source"] == "composite"
