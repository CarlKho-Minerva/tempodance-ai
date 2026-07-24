"""Interfaces shared by deterministic and remote routine analyzers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Any, Sequence


class AnalyzerUnavailable(RuntimeError):
    """Raised when an optional analysis provider cannot return a result."""


@dataclass(frozen=True, slots=True)
class RoutineSegment:
    count_start: int
    count_end: int
    focus: str
    instruction: str


@dataclass(frozen=True, slots=True)
class RoutineAnalysis:
    provider: str
    title: str
    summary: str
    segments: tuple[RoutineSegment, ...]
    degraded_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "title": self.title,
            "summary": self.summary,
            "segments": [asdict(segment) for segment in self.segments],
            "degraded_reason": self.degraded_reason,
        }


class RoutineAnalyzer(ABC):
    """Synchronous interface; API callers run remote implementations in a thread."""

    @abstractmethod
    def analyze(
        self,
        routine_url: str,
        mode: str,
        frame_data_urls: Sequence[str] = (),
    ) -> RoutineAnalysis:
        raise NotImplementedError
