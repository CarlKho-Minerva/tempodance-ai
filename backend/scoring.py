"""Pure COCO-17 pose comparison.

Public interface
----------------
``compare_poses(user_pose, reference_pose, ...)`` accepts any sequence with at
least 17 keypoints.  A keypoint may be ``[x, y]``, ``[x, y, confidence]``, a
mapping with ``x``/``y`` and ``confidence`` (or ``score``), or :class:`Keypoint`.
It returns a :class:`PoseComparison` whose ``score`` is in ``[0, 1]``.

The comparison uses unit bone direction vectors, so translation and body scale
do not affect the score.  Bones with missing/low-confidence endpoints contribute
zero rather than being silently renormalized away; ``coverage`` exposes how much
of the requested body focus was measurable.  Optional mirror comparison reflects
and swaps anatomical left/right joints, then keeps the better orientation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import math
from typing import Any, Mapping, Sequence


COCO17_NAMES: tuple[str, ...] = (
    "nose",
    "left_eye",
    "right_eye",
    "left_ear",
    "right_ear",
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
)


class Focus(str, Enum):
    """Body region emphasized by the composite score."""

    UPPER = "upper"
    LOWER = "lower"
    FULL = "full"


@dataclass(frozen=True, slots=True)
class Keypoint:
    x: float
    y: float
    confidence: float = 1.0

    @property
    def finite(self) -> bool:
        return all(math.isfinite(value) for value in (self.x, self.y, self.confidence))


@dataclass(frozen=True, slots=True)
class BoneDefinition:
    name: str
    start: int
    end: int
    group: str


# Limb vectors are stable under camera translation and body-size differences.
# Torso cross-bars are intentionally excluded: their directions change sharply
# with small camera roll while contributing little actionable dance feedback.
BONES: tuple[BoneDefinition, ...] = (
    BoneDefinition("left_upper_arm", 5, 7, "upper"),
    BoneDefinition("left_forearm", 7, 9, "upper"),
    BoneDefinition("right_upper_arm", 6, 8, "upper"),
    BoneDefinition("right_forearm", 8, 10, "upper"),
    BoneDefinition("left_thigh", 11, 13, "lower"),
    BoneDefinition("left_shin", 13, 15, "lower"),
    BoneDefinition("right_thigh", 12, 14, "lower"),
    BoneDefinition("right_shin", 14, 16, "lower"),
)


MIRROR_INDEX: tuple[int, ...] = (
    0,
    2,
    1,
    4,
    3,
    6,
    5,
    8,
    7,
    10,
    9,
    12,
    11,
    14,
    13,
    16,
    15,
)


@dataclass(frozen=True, slots=True)
class BoneScore:
    name: str
    group: str
    start_joint: str
    end_joint: str
    weight: float
    similarity: float | None
    valid: bool
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PoseComparison:
    """Result of one user/reference pose comparison."""

    score: float
    geometric_score: float
    coverage: float
    focus: Focus
    orientation: str
    bones: tuple[BoneScore, ...]

    @property
    def missing_bones(self) -> tuple[str, ...]:
        return tuple(bone.name for bone in self.bones if not bone.valid)

    @property
    def worst_bones(self) -> tuple[BoneScore, ...]:
        valid = (bone for bone in self.bones if bone.similarity is not None)
        return tuple(sorted(valid, key=lambda bone: bone.similarity or 0.0))

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "geometric_score": self.geometric_score,
            "coverage": self.coverage,
            "focus": self.focus.value,
            "orientation": self.orientation,
            "bone_scores": [bone.to_dict() for bone in self.bones],
            "missing_bones": list(self.missing_bones),
        }


RawKeypoint = Keypoint | Sequence[float] | Mapping[str, Any]
RawPose = Sequence[RawKeypoint]


def normalize_focus(value: Focus | str | None) -> Focus:
    if isinstance(value, Focus):
        return value
    normalized = str(value or "full").strip().lower().replace("-", "_")
    aliases = {
        "upper_body": Focus.UPPER,
        "arms": Focus.UPPER,
        "lower_body": Focus.LOWER,
        "legs": Focus.LOWER,
        "full_body": Focus.FULL,
        "practice": Focus.FULL,
    }
    if normalized in aliases:
        return aliases[normalized]
    try:
        return Focus(normalized)
    except ValueError:
        return Focus.FULL


def _as_float(value: Any, *, field: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Keypoint {field} must be numeric") from exc


def coerce_keypoint(value: RawKeypoint) -> Keypoint:
    if isinstance(value, Keypoint):
        return value
    if isinstance(value, Mapping):
        confidence = value.get(
            "confidence", value.get("score", value.get("visibility", 1.0))
        )
        return Keypoint(
            _as_float(value.get("x"), field="x"),
            _as_float(value.get("y"), field="y"),
            _as_float(confidence, field="confidence"),
        )
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        if len(value) < 2:
            raise ValueError("A keypoint sequence needs x and y")
        confidence = value[2] if len(value) > 2 else 1.0
        return Keypoint(
            _as_float(value[0], field="x"),
            _as_float(value[1], field="y"),
            _as_float(confidence, field="confidence"),
        )
    raise ValueError("Unsupported keypoint representation")


def coerce_pose(pose: RawPose) -> tuple[Keypoint, ...]:
    if not isinstance(pose, Sequence) or isinstance(pose, (str, bytes)):
        raise ValueError("Pose must be a sequence of COCO-17 keypoints")
    if len(pose) < len(COCO17_NAMES):
        raise ValueError(f"Expected at least 17 keypoints, received {len(pose)}")
    return tuple(coerce_keypoint(item) for item in pose[: len(COCO17_NAMES)])


def mirror_pose(pose: RawPose, *, axis_x: float | None = None) -> tuple[Keypoint, ...]:
    """Reflect a pose and swap anatomical left/right COCO joint labels."""

    points = coerce_pose(pose)
    if axis_x is None:
        finite_x = [point.x for point in points if math.isfinite(point.x)]
        axis_x = (min(finite_x) + max(finite_x)) / 2.0 if finite_x else 0.0
    mirrored: list[Keypoint] = []
    for source_index in MIRROR_INDEX:
        source = points[source_index]
        mirrored.append(
            Keypoint(2.0 * axis_x - source.x, source.y, source.confidence)
        )
    return tuple(mirrored)


def _focus_allocations(focus: Focus) -> dict[str, float]:
    if focus is Focus.UPPER:
        return {"upper": 0.8, "lower": 0.2}
    if focus is Focus.LOWER:
        return {"upper": 0.2, "lower": 0.8}
    return {"upper": 0.5, "lower": 0.5}


def _is_valid(point: Keypoint, confidence_threshold: float) -> bool:
    return point.finite and point.confidence >= confidence_threshold


def _unit_vector(start: Keypoint, end: Keypoint) -> tuple[float, float] | None:
    dx, dy = end.x - start.x, end.y - start.y
    magnitude = math.hypot(dx, dy)
    if not math.isfinite(magnitude) or magnitude <= 1e-9:
        return None
    return dx / magnitude, dy / magnitude


def _compare_once(
    user: tuple[Keypoint, ...],
    reference: tuple[Keypoint, ...],
    *,
    focus: Focus,
    confidence_threshold: float,
    orientation: str,
) -> PoseComparison:
    allocations = _focus_allocations(focus)
    counts = {
        group: sum(1 for bone in BONES if bone.group == group) for group in allocations
    }
    total_score = 0.0
    coverage = 0.0
    bone_results: list[BoneScore] = []

    for bone in BONES:
        weight = allocations[bone.group] / counts[bone.group]
        endpoints = (
            user[bone.start],
            user[bone.end],
            reference[bone.start],
            reference[bone.end],
        )
        confidence = min(point.confidence for point in endpoints)
        user_vector = None
        reference_vector = None
        if all(_is_valid(point, confidence_threshold) for point in endpoints):
            user_vector = _unit_vector(user[bone.start], user[bone.end])
            reference_vector = _unit_vector(
                reference[bone.start], reference[bone.end]
            )

        valid = user_vector is not None and reference_vector is not None
        similarity: float | None = None
        if valid and user_vector is not None and reference_vector is not None:
            cosine = user_vector[0] * reference_vector[0] + user_vector[1] * reference_vector[1]
            similarity = max(0.0, min(1.0, cosine))
            total_score += weight * similarity
            coverage += weight

        bone_results.append(
            BoneScore(
                name=bone.name,
                group=bone.group,
                start_joint=COCO17_NAMES[bone.start],
                end_joint=COCO17_NAMES[bone.end],
                weight=weight,
                similarity=similarity,
                valid=valid,
                confidence=max(0.0, min(1.0, confidence))
                if math.isfinite(confidence)
                else 0.0,
            )
        )

    geometric = total_score / coverage if coverage > 0.0 else 0.0
    return PoseComparison(
        score=max(0.0, min(1.0, total_score)),
        geometric_score=max(0.0, min(1.0, geometric)),
        coverage=max(0.0, min(1.0, coverage)),
        focus=focus,
        orientation=orientation,
        bones=tuple(bone_results),
    )


def compare_poses(
    user_pose: RawPose,
    reference_pose: RawPose,
    *,
    focus: Focus | str = Focus.FULL,
    confidence_threshold: float = 0.35,
    allow_mirror: bool = True,
) -> PoseComparison:
    """Compare two COCO-17 poses using normalized limb directions.

    ``score`` already includes a missing-data penalty: each invalid bone adds zero
    at its focus-specific weight.  ``geometric_score`` reports alignment only over
    measurable bones, while ``coverage`` reports the measurable weight.
    """

    if not 0.0 <= confidence_threshold <= 1.0:
        raise ValueError("confidence_threshold must be between 0 and 1")
    normalized_focus = normalize_focus(focus)
    user = coerce_pose(user_pose)
    reference = coerce_pose(reference_pose)
    direct = _compare_once(
        user,
        reference,
        focus=normalized_focus,
        confidence_threshold=confidence_threshold,
        orientation="direct",
    )
    if not allow_mirror:
        return direct
    mirrored = _compare_once(
        user,
        mirror_pose(reference),
        focus=normalized_focus,
        confidence_threshold=confidence_threshold,
        orientation="mirrored",
    )
    return mirrored if mirrored.score > direct.score + 1e-12 else direct
