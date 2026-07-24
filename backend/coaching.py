"""Adaptive practice state and deterministic coaching feedback."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from statistics import fmean, median
from typing import Any, Iterable, Mapping, Sequence


SPEED_TIERS: tuple[float, ...] = (0.5, 0.6, 0.8, 1.0)


@dataclass(frozen=True, slots=True)
class MasteryConfig:
    """Controls robust loop qualification.

    A loop needs enough sampled frames, sufficient trackable coverage, and a high
    fraction of frames at the score threshold.  This tolerates brief detector
    noise without allowing missing frames or one lucky sample to unlock a tier.
    """

    score_threshold: float = 0.85
    min_pose_coverage: float = 0.70
    min_frames: int = 12
    min_trackable_fraction: float = 0.80
    required_pass_fraction: float = 0.90
    consecutive_qualifying_loops: int = 2

    def __post_init__(self) -> None:
        unit_fields = (
            self.score_threshold,
            self.min_pose_coverage,
            self.min_trackable_fraction,
            self.required_pass_fraction,
        )
        if any(not 0.0 <= value <= 1.0 for value in unit_fields):
            raise ValueError("Mastery thresholds must be between 0 and 1")
        if self.min_frames < 1 or self.consecutive_qualifying_loops < 1:
            raise ValueError("Frame and loop minimums must be positive")


@dataclass(frozen=True, slots=True)
class FrameAssessment:
    score: float | None
    coverage: float


@dataclass(frozen=True, slots=True)
class LoopSummary:
    qualified: bool
    reason: str
    total_frames: int
    trackable_frames: int
    trackable_fraction: float
    passing_fraction: float
    mean_score: float
    median_score: float
    event: str
    previous_speed: float
    speed: float
    qualifying_streak: int
    mastered: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AdaptiveMastery:
    """State machine for 0.5x -> 0.6x -> 0.8x -> 1.0x practice.

    Call :meth:`record_frame` for every expected scoring sample, including a
    missing pose (``score=None``).  Call :meth:`complete_loop` at a choreography
    loop boundary.  Two qualifying loops unlock the next speed.  Two additional
    qualifying loops at 1.0x mark the routine mastered.
    """

    def __init__(self, config: MasteryConfig | None = None) -> None:
        self.config = config or MasteryConfig()
        self.tier_index = 0
        self.qualifying_streak = 0
        self.mastered = False
        self.loops_completed = 0
        self._frames: list[FrameAssessment] = []

    @property
    def speed(self) -> float:
        return SPEED_TIERS[self.tier_index]

    def record_frame(self, score: float | None, coverage: float = 1.0) -> None:
        normalized_score: float | None
        if score is None or not math.isfinite(float(score)):
            normalized_score = None
        else:
            normalized_score = max(0.0, min(1.0, float(score)))
        normalized_coverage = (
            max(0.0, min(1.0, float(coverage)))
            if math.isfinite(float(coverage))
            else 0.0
        )
        self._frames.append(FrameAssessment(normalized_score, normalized_coverage))

    def complete_loop(self) -> LoopSummary:
        previous_speed = self.speed
        total = len(self._frames)
        trackable = [
            frame.score
            for frame in self._frames
            if frame.score is not None
            and frame.coverage >= self.config.min_pose_coverage
        ]
        trackable_count = len(trackable)
        trackable_fraction = trackable_count / total if total else 0.0
        passing = [
            score for score in trackable if score >= self.config.score_threshold
        ]
        passing_fraction = len(passing) / trackable_count if trackable_count else 0.0
        mean_score = fmean(trackable) if trackable else 0.0
        median_score = median(trackable) if trackable else 0.0

        if total < self.config.min_frames:
            qualified, reason = False, "too_few_frames"
        elif trackable_fraction < self.config.min_trackable_fraction:
            qualified, reason = False, "insufficient_pose_coverage"
        elif passing_fraction < self.config.required_pass_fraction:
            qualified, reason = False, "score_consistency_below_gate"
        elif median_score < self.config.score_threshold:
            qualified, reason = False, "median_score_below_gate"
        else:
            qualified, reason = True, "qualified"

        event = "loop_qualified" if qualified else "loop_retry"
        if qualified:
            self.qualifying_streak += 1
            if self.qualifying_streak >= self.config.consecutive_qualifying_loops:
                self.qualifying_streak = 0
                if self.tier_index < len(SPEED_TIERS) - 1:
                    self.tier_index += 1
                    event = "speed_unlocked"
                else:
                    self.mastered = True
                    event = "routine_mastered"
        else:
            self.qualifying_streak = 0

        self.loops_completed += 1
        self._frames.clear()
        return LoopSummary(
            qualified=qualified,
            reason=reason,
            total_frames=total,
            trackable_frames=trackable_count,
            trackable_fraction=trackable_fraction,
            passing_fraction=passing_fraction,
            mean_score=mean_score,
            median_score=median_score,
            event=event,
            previous_speed=previous_speed,
            speed=self.speed,
            qualifying_streak=self.qualifying_streak,
            mastered=self.mastered,
        )

    def state(self) -> dict[str, Any]:
        return {
            "speed": self.speed,
            "speed_tier": f"{self.speed:.1f}x",
            "tier_index": self.tier_index,
            "tiers": list(SPEED_TIERS),
            "qualifying_streak": self.qualifying_streak,
            "required_qualifying_loops": self.config.consecutive_qualifying_loops,
            "mastered": self.mastered,
            "loops_completed": self.loops_completed,
            "frames_in_loop": len(self._frames),
            "gate": {
                "score_threshold": self.config.score_threshold,
                "min_pose_coverage": self.config.min_pose_coverage,
                "min_frames": self.config.min_frames,
                "min_trackable_fraction": self.config.min_trackable_fraction,
                "required_pass_fraction": self.config.required_pass_fraction,
            },
        }


def _iter_bones(bone_scores: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(bone_scores, Mapping):
        if "bone_scores" in bone_scores:
            yield from _iter_bones(bone_scores["bone_scores"])
            return
        for name, value in bone_scores.items():
            if isinstance(value, Mapping):
                yield {"name": name, **value}
            elif isinstance(value, (int, float)):
                yield {"name": name, "similarity": value}
        return
    if isinstance(bone_scores, Sequence) and not isinstance(
        bone_scores, (str, bytes)
    ):
        for value in bone_scores:
            if isinstance(value, Mapping):
                yield value


def deterministic_coaching(
    score: float | None,
    bone_scores: Any = None,
    *,
    coverage: float = 1.0,
    mastered: bool = False,
    preferred_bone: str | None = None,
) -> dict[str, str]:
    """Return stable, judge-demo-safe feedback without an external model."""

    if mastered:
        return {"level": "mastered", "message": "Full-speed routine locked in."}
    if score is None or coverage < 0.5:
        return {
            "level": "tracking",
            "message": "Step back until your wrists and ankles are visible.",
        }

    valid_bones = [
        bone
        for bone in _iter_bones(bone_scores)
        if isinstance(bone.get("similarity"), (int, float))
    ]
    worst = min(valid_bones, key=lambda bone: float(bone["similarity"]), default=None)
    target_name = preferred_bone or (str(worst.get("name")) if worst else "pose")
    target = target_name.replace("_", " ")

    if score >= 0.90:
        return {"level": "excellent", "message": "Clean shape. Keep the timing steady."}
    if score >= 0.85:
        return {"level": "passing", "message": "On target. Repeat it once more."}
    if score >= 0.65:
        return {
            "level": "adjust",
            "message": f"Close. Match the {target} angle on the next count.",
        }
    return {
        "level": "reset",
        "message": f"Reset the count and isolate your {target} first.",
    }
