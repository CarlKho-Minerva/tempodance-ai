"""In-memory practice session coordination.

The storage boundary is intentionally small.  A database-backed implementation
can replace :class:`SessionStore` later without changing scoring or API payloads.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from statistics import median
import threading
from typing import Any, Iterable, Mapping, Sequence
import uuid

from .analyzers.base import RoutineAnalysis
from .coaching import AdaptiveMastery, LoopSummary, deterministic_coaching
from .scoring import normalize_focus


@dataclass(slots=True)
class PracticeSession:
    id: str
    routine_url: str
    mode: str
    analysis: RoutineAnalysis
    mastery: AdaptiveMastery = field(default_factory=AdaptiveMastery)
    last_count: int | None = None
    last_score: float | None = None
    last_coverage: float = 0.0
    policy_revision: int = 0
    policy_focus_bone: str | None = None
    policy_target_baseline: float | None = None
    policy_intervention: str = "full_body_scan"
    joint_ema: dict[str, float] = field(default_factory=dict)
    joint_samples: dict[str, int] = field(default_factory=dict)
    memory_events: list[dict[str, Any]] = field(default_factory=list)
    _loop_bone_values: dict[str, list[float]] = field(default_factory=dict, repr=False)
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    @staticmethod
    def _iter_bone_scores(bone_scores: Any) -> Iterable[tuple[str, float]]:
        if isinstance(bone_scores, Mapping):
            if "bone_scores" in bone_scores:
                yield from PracticeSession._iter_bone_scores(bone_scores["bone_scores"])
                return
            for name, value in bone_scores.items():
                if isinstance(value, Mapping):
                    similarity = value.get("similarity")
                else:
                    similarity = value
                if isinstance(similarity, (int, float)) and math.isfinite(float(similarity)):
                    yield str(name), max(0.0, min(1.0, float(similarity)))
            return
        if isinstance(bone_scores, Sequence) and not isinstance(
            bone_scores, (str, bytes)
        ):
            for item in bone_scores:
                if not isinstance(item, Mapping) or item.get("valid") is False:
                    continue
                name, similarity = item.get("name"), item.get("similarity")
                if name and isinstance(similarity, (int, float)) and math.isfinite(float(similarity)):
                    yield str(name), max(0.0, min(1.0, float(similarity)))

    def _remember_bones(self, bone_scores: Any) -> None:
        # EMA favors recent loops while retaining session-level teaching memory.
        alpha = 0.25
        for name, similarity in self._iter_bone_scores(bone_scores):
            previous = self.joint_ema.get(name)
            self.joint_ema[name] = (
                similarity if previous is None else alpha * similarity + (1.0 - alpha) * previous
            )
            self.joint_samples[name] = self.joint_samples.get(name, 0) + 1
            self._loop_bone_values.setdefault(name, []).append(similarity)

    @property
    def ema_weakest_bone(self) -> str | None:
        return min(self.joint_ema, key=self.joint_ema.get) if self.joint_ema else None

    @property
    def weakest_bone(self) -> str | None:
        # Once a loop has completed, the policy target is based on that loop's
        # reliable aggregate. Before then, the frame-level EMA is a useful preview.
        return self.policy_focus_bone or self.ema_weakest_bone

    @property
    def policy_version(self) -> str:
        return f"1.{self.policy_revision}"

    def _next_intervention(self, *, same_target: bool) -> str:
        strategies = ("isolate_angle", "slow_hold", "count_anchor")
        if not same_target or self.policy_intervention not in strategies:
            return strategies[0]
        index = strategies.index(self.policy_intervention)
        return strategies[(index + 1) % len(strategies)]

    def _evolve_policy(self, summary: LoopSummary) -> None:
        """Evaluate the prior intervention, then retain or revise it.

        The target metric is the median score of the selected bone within a loop.
        At least half of the loop's frames (and at least three samples) must contain
        that bone before it can drive a policy change.  A +0.015 target delta is
        required to retain an intervention.  These choices affect coaching
        attention only; scoring weights and mastery thresholds never change.
        """

        required_samples = max(3, math.ceil(summary.total_frames * 0.5))
        aggregates = {
            name: median(values)
            for name, values in self._loop_bone_values.items()
            if len(values) >= required_samples
        }
        self._loop_bone_values.clear()
        evidence_reliable = summary.total_frames >= self.mastery.config.min_frames and bool(aggregates)
        previous_target = self.policy_focus_bone
        previous_baseline = self.policy_target_baseline
        previous_intervention = self.policy_intervention
        evaluated_value = aggregates.get(previous_target) if previous_target else None
        target_delta = (
            evaluated_value - previous_baseline
            if evaluated_value is not None and previous_baseline is not None
            else None
        )
        minimum_delta = 0.015

        if not evidence_reliable:
            decision = "held_insufficient_evidence"
            reason = "The loop lacked enough reliable per-bone samples."
            next_target = previous_target
            next_intervention = previous_intervention
        elif previous_target is None:
            decision = "initialized"
            reason = "The first reliable loop established a personalized weak-motion baseline."
            next_target = min(aggregates, key=aggregates.get)
            next_intervention = self._next_intervention(same_target=False)
        elif target_delta is not None and target_delta >= minimum_delta:
            decision = "retained"
            reason = "The targeted motion improved enough to retain this intervention."
            next_target = previous_target
            next_intervention = previous_intervention
        else:
            decision = "revised"
            reason = (
                "The targeted motion did not improve enough, so the next intervention changed."
                if target_delta is not None
                else "The prior target was not measurable, so the policy moved to reliable evidence."
            )
            next_target = min(aggregates, key=aggregates.get)
            next_intervention = self._next_intervention(
                same_target=next_target == previous_target
            )

        self.policy_focus_bone = next_target
        self.policy_intervention = next_intervention
        self.policy_target_baseline = aggregates.get(next_target, previous_baseline)
        self.policy_revision += 1
        target_label = next_target.replace("_", " ").title() if next_target else "Policy"
        titles = {
            "initialized": f"Baseline found: {target_label}",
            "retained": f"Cue retained: {target_label}",
            "revised": f"Cue revised: {target_label}",
            "held_insufficient_evidence": "Policy held: more evidence needed",
        }
        self.memory_events.append(
            {
                "title": titles[decision],
                "detail": reason,
                "score": (
                    f"{target_delta:+.1%}" if target_delta is not None else "baseline"
                ),
                "loop": self.mastery.loops_completed,
                "qualified": summary.qualified,
                "event": summary.event,
                "decision": decision,
                "reason": reason,
                "evaluated_target": previous_target,
                "target_before": previous_baseline,
                "target_after": evaluated_value,
                "target_delta": target_delta,
                "retention_delta_required": minimum_delta,
                "previous_intervention": previous_intervention,
                "next_target": next_target,
                "next_target_baseline": self.policy_target_baseline,
                "next_intervention": next_intervention,
                "loop_bone_medians": dict(sorted(aggregates.items())),
                "policy_version": self.policy_version,
            }
        )
        del self.memory_events[:-12]

    def learning_payload(self) -> dict[str, Any]:
        with self._lock:
            weakest = self.weakest_bone
            target_label = weakest.replace("_", " ") if weakest else "full body"
            rules = {
                "full_body_scan": "Scan the full body equally until a stable weak point appears.",
                "isolate_angle": f"Isolate the {target_label} angle before adding full-body timing.",
                "slow_hold": f"Hold the {target_label} shape for one extra beat, then release.",
                "count_anchor": f"Anchor the {target_label} correction precisely on counts four and eight.",
            }
            rule = rules.get(self.policy_intervention, rules["full_body_scan"])
            known_bones = sorted(self.joint_ema)
            if weakest and known_bones:
                remaining = [name for name in known_bones if name != weakest]
                attention_weights = {weakest: 1.0 if not remaining else 0.5}
                if remaining:
                    attention_weights.update(
                        {name: 0.5 / len(remaining) for name in remaining}
                    )
            else:
                attention_weights = {
                    name: 1.0 / len(known_bones) for name in known_bones
                } if known_bones else {}
            latest_event = self.memory_events[-1] if self.memory_events else None
            memory = {
                "signal_count": sum(self.joint_samples.values()),
                "weakest_bone": weakest,
                "joint_ema": dict(sorted(self.joint_ema.items())),
                "events": list(self.memory_events),
            }
            policy = {
                "version": self.policy_version,
                "revision": self.policy_revision,
                "focus_bone": weakest,
                "intervention": self.policy_intervention,
                "target_baseline": self.policy_target_baseline,
                "attention_weights": attention_weights,
                "rule": rule,
                "safe_scope": "coaching_only",
                "last_decision": latest_event["decision"] if latest_event else "collecting_baseline",
                "last_target_delta": latest_event["target_delta"] if latest_event else None,
            }
            return {
                "policy_version": self.policy_version,
                "weakest_bone": weakest,
                "joint_ema": memory["joint_ema"],
                "memory_count": memory["signal_count"],
                "memories": memory["events"],
                "session_memory": memory["events"],
                "clean_loops": self.mastery.qualifying_streak,
                "mastery_streak": self.mastery.qualifying_streak,
                "policy_decision": policy["last_decision"],
                "target_delta": policy["last_target_delta"],
                "intervention": self.policy_intervention,
                "memory": memory,
                "policy": policy,
            }

    def process_observation(
        self,
        score: float | None,
        coverage: float,
        *,
        should_record: bool,
        bone_scores: Any = None,
        count: int | None = None,
        loop_complete: bool = False,
    ) -> LoopSummary | None:
        """Atomically record a sample and apply explicit/count-wrap loop gates."""

        with self._lock:
            summary: LoopSummary | None = None
            wrapped = (
                count is not None
                and self.last_count is not None
                and self.last_count >= 7
                and count <= 2
            )
            if wrapped and self.mastery.state()["frames_in_loop"]:
                summary = self.mastery.complete_loop()
                self._evolve_policy(summary)
            if count is not None:
                self.last_count = count
            if should_record:
                self.mastery.record_frame(score, coverage)
                self.last_score = score
                self.last_coverage = coverage
                self._remember_bones(bone_scores)
            if loop_complete and not wrapped and self.mastery.state()["frames_in_loop"]:
                summary = self.mastery.complete_loop()
                self._evolve_policy(summary)
            return summary

    def complete_loop(self) -> LoopSummary:
        with self._lock:
            summary = self.mastery.complete_loop()
            self._evolve_policy(summary)
            return summary

    def payload(self) -> dict[str, Any]:
        with self._lock:
            state = self.mastery.state()
            return {
                "id": self.id,
                "session_id": self.id,
                "routine_url": self.routine_url,
                "mode": self.mode,
                "analysis": self.analysis.to_dict(),
                "state": state,
                "speed": state["speed"],
                "last_score": self.last_score,
                "last_coverage": self.last_coverage,
                "coaching": deterministic_coaching(
                    self.last_score,
                    coverage=self.last_coverage,
                    mastered=state["mastered"],
                    preferred_bone=self.policy_focus_bone,
                ),
                **self.learning_payload(),
            }


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, PracticeSession] = {}
        self._lock = threading.RLock()

    def create(
        self, routine_url: str, mode: str, analysis: RoutineAnalysis
    ) -> PracticeSession:
        session = PracticeSession(
            id=uuid.uuid4().hex,
            routine_url=routine_url,
            mode=normalize_focus(mode).value,
            analysis=analysis,
        )
        with self._lock:
            self._sessions[session.id] = session
        return session

    def get(self, session_id: str) -> PracticeSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def count(self) -> int:
        with self._lock:
            return len(self._sessions)
