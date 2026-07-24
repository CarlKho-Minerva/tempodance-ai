from __future__ import annotations

import unittest

from backend.coaching import AdaptiveMastery, MasteryConfig, deterministic_coaching


def test_config() -> MasteryConfig:
    return MasteryConfig(
        min_frames=5,
        min_trackable_fraction=0.8,
        required_pass_fraction=0.8,
        consecutive_qualifying_loops=2,
    )


def fill_loop(state: AdaptiveMastery, scores: list[float | None], coverage: float = 1.0):
    for score in scores:
        state.record_frame(score, coverage if score is not None else 0.0)
    return state.complete_loop()


class AdaptiveMasteryTests(unittest.TestCase):
    def test_two_consistent_loops_unlock_next_speed(self) -> None:
        state = AdaptiveMastery(test_config())
        first = fill_loop(state, [0.9] * 5)
        second = fill_loop(state, [0.9] * 5)
        self.assertTrue(first.qualified)
        self.assertEqual(first.event, "loop_qualified")
        self.assertEqual(second.event, "speed_unlocked")
        self.assertEqual(state.speed, 0.6)
        self.assertEqual(state.qualifying_streak, 0)

    def test_failure_resets_qualifying_streak(self) -> None:
        state = AdaptiveMastery(test_config())
        fill_loop(state, [0.9] * 5)
        failed = fill_loop(state, [0.4] * 5)
        self.assertFalse(failed.qualified)
        self.assertEqual(state.qualifying_streak, 0)
        fill_loop(state, [0.9] * 5)
        self.assertEqual(state.speed, 0.5)

    def test_gate_rejects_too_few_and_untrackable_frames(self) -> None:
        state = AdaptiveMastery(test_config())
        short = fill_loop(state, [0.95] * 4)
        self.assertEqual(short.reason, "too_few_frames")
        sparse = fill_loop(state, [0.95, 0.95, 0.95, None, None])
        self.assertEqual(sparse.reason, "insufficient_pose_coverage")

    def test_single_detector_outlier_is_tolerated(self) -> None:
        state = AdaptiveMastery(test_config())
        summary = fill_loop(state, [0.92, 0.93, 0.2, 0.91, 0.94])
        self.assertTrue(summary.qualified)
        self.assertAlmostEqual(summary.passing_fraction, 0.8)

    def test_full_speed_requires_its_own_mastery_loops(self) -> None:
        state = AdaptiveMastery(test_config())
        for _ in range(6):
            fill_loop(state, [0.95] * 5)
        self.assertEqual(state.speed, 1.0)
        self.assertFalse(state.mastered)
        fill_loop(state, [0.95] * 5)
        final = fill_loop(state, [0.95] * 5)
        self.assertTrue(state.mastered)
        self.assertEqual(final.event, "routine_mastered")

    def test_deterministic_coaching_targets_worst_bone(self) -> None:
        message = deterministic_coaching(
            0.7,
            [
                {"name": "left_forearm", "similarity": 0.3},
                {"name": "right_thigh", "similarity": 0.8},
            ],
        )
        self.assertEqual(message["level"], "adjust")
        self.assertIn("left forearm", message["message"])


if __name__ == "__main__":
    unittest.main()
