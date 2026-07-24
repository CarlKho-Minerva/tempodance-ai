"""Deterministic routine plan used for offline and failure-safe demos."""

from __future__ import annotations

from typing import Sequence

from .base import RoutineAnalysis, RoutineAnalyzer, RoutineSegment


class DeterministicAnalyzer(RoutineAnalyzer):
    def __init__(self, degraded_reason: str | None = None) -> None:
        self.degraded_reason = degraded_reason

    def analyze(
        self,
        routine_url: str,
        mode: str,
        frame_data_urls: Sequence[str] = (),
    ) -> RoutineAnalysis:
        focus = mode if mode in {"upper", "lower", "full"} else "full"
        segments = (
            RoutineSegment(1, 2, focus, "Mark the starting shape and settle your weight."),
            RoutineSegment(3, 4, focus, "Trace the main arm line while keeping the torso quiet."),
            RoutineSegment(5, 6, focus, "Transfer weight and finish both leg lines."),
            RoutineSegment(7, 8, focus, "Hit the final shape, then return to count one."),
        )
        return RoutineAnalysis(
            provider="deterministic",
            title="TempoDance 8-count practice loop",
            summary="A stable four-part fallback plan for live pose practice.",
            segments=segments,
            degraded_reason=self.degraded_reason,
        )
