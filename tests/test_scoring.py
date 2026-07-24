from __future__ import annotations

import math
import unittest

from backend.scoring import Keypoint, compare_poses, mirror_pose


def sample_pose(confidence: float = 1.0) -> list[list[float]]:
    # COCO-17 with deliberately asymmetric limb angles.
    points = [[0.0, 0.0, confidence] for _ in range(17)]
    points[5] = [-1.0, 0.0, confidence]
    points[7] = [-2.1, 0.7, confidence]
    points[9] = [-2.3, 2.1, confidence]
    points[6] = [1.0, 0.0, confidence]
    points[8] = [1.4, -1.1, confidence]
    points[10] = [2.5, -1.0, confidence]
    points[11] = [-0.7, 2.0, confidence]
    points[13] = [-0.9, 4.2, confidence]
    points[15] = [-1.5, 6.0, confidence]
    points[12] = [0.7, 2.0, confidence]
    points[14] = [1.5, 3.5, confidence]
    points[16] = [1.1, 5.8, confidence]
    return points


class PoseScoringTests(unittest.TestCase):
    def test_identical_pose_scores_one(self) -> None:
        result = compare_poses(sample_pose(), sample_pose(), allow_mirror=False)
        self.assertAlmostEqual(result.score, 1.0)
        self.assertAlmostEqual(result.coverage, 1.0)
        self.assertEqual(result.orientation, "direct")
        self.assertFalse(result.missing_bones)

    def test_translation_and_scale_do_not_change_score(self) -> None:
        reference = sample_pose()
        transformed = [
            [point[0] * 3.7 + 120.0, point[1] * 3.7 - 42.0, point[2]]
            for point in reference
        ]
        result = compare_poses(transformed, reference, allow_mirror=False)
        self.assertAlmostEqual(result.score, 1.0, places=7)

    def test_focus_weights_change_composite_score(self) -> None:
        reference = sample_pose()
        user = [point[:] for point in reference]
        # Reverse every leg vector while leaving arms untouched.
        user[13] = [-0.5, -0.2, 1.0]
        user[15] = [0.1, -2.0, 1.0]
        user[14] = [-0.1, 0.5, 1.0]
        user[16] = [-0.5, -1.8, 1.0]
        upper = compare_poses(user, reference, focus="upper", allow_mirror=False)
        lower = compare_poses(user, reference, focus="lower", allow_mirror=False)
        self.assertGreater(upper.score, lower.score)
        self.assertAlmostEqual(upper.score, 0.8, places=6)
        self.assertAlmostEqual(lower.score, 0.2, places=6)

    def test_missing_low_confidence_bone_reduces_coverage_and_score(self) -> None:
        user = sample_pose()
        user[9][2] = 0.1
        result = compare_poses(
            user,
            sample_pose(),
            confidence_threshold=0.35,
            allow_mirror=False,
        )
        self.assertAlmostEqual(result.coverage, 0.875)
        self.assertAlmostEqual(result.score, 0.875)
        self.assertIn("left_forearm", result.missing_bones)

    def test_mirror_mode_recovers_visual_mirroring(self) -> None:
        reference = sample_pose()
        user = mirror_pose(reference)
        direct = compare_poses(user, reference, allow_mirror=False)
        mirrored = compare_poses(user, reference, allow_mirror=True)
        self.assertLess(direct.score, 0.9)
        self.assertAlmostEqual(mirrored.score, 1.0, places=7)
        self.assertEqual(mirrored.orientation, "mirrored")

    def test_invalid_pose_and_threshold_raise_clear_errors(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 17"):
            compare_poses([[0, 0]], sample_pose())
        with self.assertRaisesRegex(ValueError, "between 0 and 1"):
            compare_poses(sample_pose(), sample_pose(), confidence_threshold=2.0)

    def test_nonfinite_endpoint_is_missing_not_a_crash(self) -> None:
        user = sample_pose()
        user[10][0] = math.nan
        result = compare_poses(user, sample_pose(), allow_mirror=False)
        self.assertIn("right_forearm", result.missing_bones)
        self.assertLess(result.score, 1.0)


if __name__ == "__main__":
    unittest.main()
