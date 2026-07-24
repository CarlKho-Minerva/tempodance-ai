"""Routine-analysis provider selection."""

from __future__ import annotations

import os

from .base import AnalyzerUnavailable, RoutineAnalyzer
from .fallback import DeterministicAnalyzer
from .fireworks import FireworksAnalyzer


def build_analyzer(provider: str | None = None) -> RoutineAnalyzer:
    """Build an analyzer without silently treating coupons as credentials.

    Remote analysis is opt-in through ``provider='fireworks'`` (or
    ``TEMPO_ANALYZER_PROVIDER=fireworks``) and requires a real value in the
    standard ``FIREWORKS_API_KEY`` environment variable.
    """

    selected = (provider or os.getenv("TEMPO_ANALYZER_PROVIDER", "local")).lower()
    if selected in {"fireworks", "ai", "remote"}:
        api_key = os.getenv("FIREWORKS_API_KEY", "").strip()
        if not api_key:
            raise AnalyzerUnavailable("FIREWORKS_API_KEY is not configured")
        return FireworksAnalyzer(api_key=api_key)
    return DeterministicAnalyzer()


__all__ = [
    "AnalyzerUnavailable",
    "DeterministicAnalyzer",
    "FireworksAnalyzer",
    "RoutineAnalyzer",
    "build_analyzer",
]
