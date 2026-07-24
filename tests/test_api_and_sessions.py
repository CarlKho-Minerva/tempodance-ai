from __future__ import annotations

import asyncio
import os
import unittest
from unittest.mock import patch

from backend.analyzers import AnalyzerUnavailable, build_analyzer
from backend.analyzers.fallback import DeterministicAnalyzer
from backend.main import (
    app,
    complete_session_loop,
    create_session,
    health,
    observe_session,
)
from backend.pose_engine import PoseEngine
from backend.schemas import LoopCompleteRequest, ObservationRequest, SessionCreate
from backend.sessions import SessionStore


class ApiAndSessionTests(unittest.TestCase):
    def test_pose_engine_does_not_load_model_at_construction(self) -> None:
        engine = PoseEngine(model_name="never-loaded.pt")
        self.assertFalse(engine.is_loaded)
        self.assertTrue(engine.status()["lazy"])

    def test_no_remote_key_selects_fallback_or_clear_error(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsInstance(build_analyzer(), DeterministicAnalyzer)
            with self.assertRaises(AnalyzerUnavailable):
                build_analyzer("fireworks")

    def test_session_store_returns_tolerant_payload(self) -> None:
        analysis = DeterministicAnalyzer().analyze("demo", "full")
        store = SessionStore()
        session = store.create("demo", "full", analysis)
        payload = session.payload()
        self.assertEqual(payload["id"], payload["session_id"])
        self.assertEqual(payload["speed"], 0.5)
        self.assertEqual(store.get(session.id), session)

    def test_fastapi_routes_are_registered(self) -> None:
        paths = {route.path for route in app.routes}
        self.assertIn("/api/sessions", paths)
        self.assertIn("/api/sessions/{session_id}/observe", paths)
        self.assertIn("/ws/pose", paths)
        self.assertIn("/api/health", paths)
        self.assertTrue(any(route.name == "frontend" for route in app.routes))

    def test_create_and_observe_direct_score_without_pose_model(self) -> None:
        request = SessionCreate(
            routine_url="https://example.test/routine",
            mode="full",
            frontend_experiment="accepted-extra-field",
        )
        created = asyncio.run(create_session(request))
        observed = asyncio.run(
            observe_session(
                created["session_id"],
                ObservationRequest(
                    score=92,
                    bone_scores={"left_forearm": 0.7},
                    count="1",
                    another_extra=True,
                ),
            )
        )
        self.assertAlmostEqual(observed["score"], 0.92)
        self.assertEqual(observed["session_id"], created["session_id"])
        self.assertEqual(observed["state"]["frames_in_loop"], 1)
        self.assertEqual(observed["weakest_bone"], "left_forearm")
        self.assertEqual(observed["policy_version"], "1.0")

    def test_null_routine_url_is_accepted_for_camera_mode(self) -> None:
        created = asyncio.run(create_session(SessionCreate(routine_url=None, mode="camera")))
        self.assertEqual(created["routine_url"], "")
        self.assertEqual(created["mode"], "full")

    def test_api_loop_completion_evolves_visible_policy(self) -> None:
        created = asyncio.run(create_session(SessionCreate(routine_url="demo", mode="full")))
        session_id = created["session_id"]
        for _ in range(12):
            asyncio.run(
                observe_session(
                    session_id,
                    ObservationRequest(
                        score=0.9,
                        coverage=1.0,
                        bone_scores={"left_forearm": 0.72, "right_thigh": 0.94},
                    ),
                )
            )
        completed = asyncio.run(
            complete_session_loop(session_id, LoopCompleteRequest())
        )
        self.assertTrue(completed["loop"]["qualified"])
        self.assertEqual(completed["policy_version"], "1.1")
        self.assertEqual(completed["weakest_bone"], "left_forearm")
        self.assertEqual(len(completed["session_memory"]), 1)
        self.assertEqual(completed["memories"][0]["title"], "Baseline found: Left Forearm")
        self.assertEqual(completed["policy_decision"], "initialized")
        self.assertEqual(completed["intervention"], "isolate_angle")

    def test_policy_retains_only_after_measured_target_improvement(self) -> None:
        created = asyncio.run(create_session(SessionCreate(routine_url="demo", mode="full")))
        session_id = created["session_id"]

        def run_loop(left_forearm: float):
            for _ in range(12):
                asyncio.run(
                    observe_session(
                        session_id,
                        ObservationRequest(
                            score=0.88,
                            coverage=1.0,
                            bone_scores={
                                "left_forearm": left_forearm,
                                "right_thigh": 0.92,
                            },
                        ),
                    )
                )
            return asyncio.run(
                complete_session_loop(session_id, LoopCompleteRequest())
            )

        baseline = run_loop(0.60)
        improved = run_loop(0.68)
        stalled = run_loop(0.67)
        self.assertEqual(baseline["policy_decision"], "initialized")
        self.assertEqual(improved["policy_decision"], "retained")
        self.assertAlmostEqual(improved["target_delta"], 0.08)
        self.assertEqual(stalled["policy_decision"], "revised")
        self.assertAlmostEqual(stalled["target_delta"], -0.01)
        self.assertNotEqual(
            stalled["policy"]["intervention"],
            improved["policy"]["intervention"],
        )

    def test_health_does_not_force_model_loading(self) -> None:
        result = asyncio.run(health())
        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["pose_engine"]["lazy"])


if __name__ == "__main__":
    unittest.main()
