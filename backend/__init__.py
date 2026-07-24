"""TempoDance backend package.

The package deliberately keeps scoring and coaching independent from FastAPI and
Ultralytics.  That makes the core behavior deterministic, unit-testable, and
usable in a local demo even when the pose model or a remote provider is absent.
"""

from .coaching import AdaptiveMastery, MasteryConfig
from .scoring import Focus, Keypoint, PoseComparison, compare_poses

__all__ = [
    "AdaptiveMastery",
    "Focus",
    "Keypoint",
    "MasteryConfig",
    "PoseComparison",
    "compare_poses",
]
