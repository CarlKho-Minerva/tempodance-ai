"""FastAPI entrypoint for TempoDance local and hosted demos.

HTTP contracts
--------------
* ``POST /api/sessions`` creates a practice session from ``routine_url``/``mode``.
* ``POST /api/sessions/{id}/observe`` accepts a direct score or a base64 frame
  plus COCO-17 ``reference_keypoints``.
* ``POST /api/sessions/{id}/loops/complete`` closes the current mastery loop.
* ``WS /ws/pose`` accepts JSON with ``frame``, ``reference`` and ``session_id``.

All request models allow extra fields so the frontend can evolve during the
hackathon without turning additive payload changes into HTTP 422 responses.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .analyzers import AnalyzerUnavailable, build_analyzer
from .analyzers.fallback import DeterministicAnalyzer
from .coaching import deterministic_coaching
from .pose_engine import PoseEngine, PoseEngineError, decode_image_data
from .schemas import LoopCompleteRequest, ObservationRequest, SessionCreate
from .scoring import PoseComparison, compare_poses, normalize_focus
from .sessions import PracticeSession, SessionStore


app = FastAPI(
    title="TempoDance AI",
    version="0.1.0",
    description="Real-time pose scoring and adaptive 8-count dance coaching.",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "TEMPO_ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions = SessionStore()
pose_engine = PoseEngine()


def _session_or_404(session_id: str) -> PracticeSession:
    session = sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Practice session not found")
    return session


def _normalize_score(score: float | None) -> float | None:
    if score is None:
        return None
    value = float(score)
    # Tolerate UI percentages while keeping the canonical API in [0, 1].
    if 1.0 < value <= 100.0:
        value /= 100.0
    return max(0.0, min(1.0, value))


def _parse_count(value: int | str | None) -> int | None:
    if value is None:
        return None
    try:
        count = int(value)
    except (TypeError, ValueError):
        return None
    return count if 1 <= count <= 8 else None


def _comparison_payload(comparison: PoseComparison | None) -> dict[str, Any]:
    if comparison is None:
        return {}
    detail = comparison.to_dict()
    bone_details = detail.pop("bone_scores")
    # The static frontend consumes a name -> scalar map. Preserve richer records
    # separately for debugging and future heat-map UIs.
    detail["bone_scores"] = {
        bone["name"]: bone["similarity"]
        for bone in bone_details
        if bone["similarity"] is not None
    }
    detail["bone_details"] = bone_details
    return detail


async def _analyze_session(request: SessionCreate):
    routine_url = request.routine_url or ""
    try:
        analyzer = build_analyzer(request.analysis_provider)
    except AnalyzerUnavailable as exc:
        analyzer = DeterministicAnalyzer(degraded_reason=str(exc))
    try:
        return await asyncio.to_thread(
            analyzer.analyze,
            routine_url,
            normalize_focus(request.mode).value,
            request.frame_data_urls,
        )
    except AnalyzerUnavailable as exc:
        fallback = DeterministicAnalyzer(degraded_reason=str(exc))
        return fallback.analyze(routine_url, normalize_focus(request.mode).value)


@app.get("/health")
@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "tempodance-api",
        "pose_engine": pose_engine.status(),
        "sessions": sessions.count(),
    }


@app.post("/api/sessions")
async def create_session(request: SessionCreate) -> dict[str, Any]:
    analysis = await _analyze_session(request)
    session = sessions.create(request.routine_url or "", request.mode, analysis)
    return session.payload()


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str) -> dict[str, Any]:
    return _session_or_404(session_id).payload()


async def _infer_comparison(
    frame_data: str,
    reference: list[Any] | None,
    *,
    focus: str,
    confidence_threshold: float,
    allow_mirror: bool,
) -> tuple[Any, PoseComparison | None]:
    frame = decode_image_data(frame_data)
    observation = await asyncio.to_thread(pose_engine.extract, frame)
    comparison = None
    if observation is not None and reference is not None:
        comparison = compare_poses(
            observation.keypoints,
            reference,
            focus=focus,
            confidence_threshold=confidence_threshold,
            allow_mirror=allow_mirror,
        )
    return observation, comparison


@app.post("/api/sessions/{session_id}/observe")
async def observe_session(
    session_id: str, request: ObservationRequest
) -> dict[str, Any]:
    session = _session_or_404(session_id)
    frame_data = request.frame_base64 or request.frame
    reference = (
        request.reference_keypoints
        if request.reference_keypoints is not None
        else request.reference
    )
    observation = None
    comparison: PoseComparison | None = None
    score = _normalize_score(request.score)
    coverage = request.coverage if request.coverage is not None else (1.0 if score is not None else 0.0)
    bone_scores = request.bone_scores

    if frame_data:
        try:
            observation, comparison = await _infer_comparison(
                frame_data,
                reference,
                focus=request.focus or session.mode,
                confidence_threshold=request.confidence_threshold,
                allow_mirror=request.allow_mirror,
            )
        except (PoseEngineError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if comparison is not None:
            score = comparison.score
            coverage = comparison.coverage
            bone_scores = _comparison_payload(comparison)["bone_scores"]
        elif observation is None and reference is not None:
            score, coverage = None, 0.0

    should_record = score is not None or (frame_data is not None and reference is not None)
    summary = session.process_observation(
        score,
        float(coverage),
        should_record=should_record,
        bone_scores=bone_scores,
        count=_parse_count(request.count),
        loop_complete=request.loop_complete,
    )
    state = session.mastery.state()
    status = "success" if observation is not None or score is not None else "no_pose_detected"
    result: dict[str, Any] = {
        "status": status,
        "id": session.id,
        "session_id": session.id,
        "score": score,
        "coverage": coverage,
        "bone_scores": bone_scores,
        "state": state,
        "speed": state["speed"],
        "loop": summary.to_dict() if summary else None,
        "coaching": deterministic_coaching(
            score,
            bone_scores,
            coverage=float(coverage),
            mastered=state["mastered"],
            preferred_bone=session.policy_focus_bone,
        ),
        **_comparison_payload(comparison),
        **session.learning_payload(),
    }
    if observation is not None:
        result.update(observation.to_dict())
    return result


@app.post("/api/sessions/{session_id}/loops/complete")
async def complete_session_loop(
    session_id: str, request: LoopCompleteRequest | None = None
) -> dict[str, Any]:
    session = _session_or_404(session_id)
    summary = session.complete_loop()
    return {
        "id": session.id,
        "session_id": session.id,
        "loop": summary.to_dict(),
        "state": session.mastery.state(),
        "speed": session.mastery.speed,
        **session.learning_payload(),
    }


def _websocket_reference(payload: dict[str, Any]) -> list[Any] | None:
    for field in ("reference_keypoints", "reference"):
        value = payload.get(field)
        if isinstance(value, list):
            return value
    return None


@app.websocket("/ws/pose")
async def pose_websocket(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
                if not isinstance(payload, dict):
                    raise ValueError
            except (json.JSONDecodeError, ValueError):
                payload = {"frame": raw}

            if payload.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue
            session_id = str(payload.get("session_id", ""))
            session = sessions.get(session_id) if session_id else None
            if session_id and session is None:
                await websocket.send_json(
                    {"status": "error", "code": "session_not_found", "session_id": session_id}
                )
                continue
            frame_data = (
                payload.get("frame")
                or payload.get("frame_base64")
                or payload.get("image")
            )
            if not isinstance(frame_data, str):
                await websocket.send_json(
                    {"status": "error", "code": "frame_required", "session_id": session_id or None}
                )
                continue
            reference = _websocket_reference(payload)
            focus = str(payload.get("focus") or (session.mode if session else "full"))
            try:
                observation, comparison = await _infer_comparison(
                    frame_data,
                    reference,
                    focus=focus,
                    confidence_threshold=float(payload.get("confidence_threshold", 0.35)),
                    allow_mirror=bool(payload.get("allow_mirror", True)),
                )
            except (PoseEngineError, ValueError) as exc:
                await websocket.send_json(
                    {
                        "status": "error",
                        "code": "pose_processing_failed",
                        "message": str(exc),
                        "session_id": session_id or None,
                    }
                )
                continue

            score = comparison.score if comparison else None
            coverage = comparison.coverage if comparison else 0.0
            bone_scores = _comparison_payload(comparison).get("bone_scores") if comparison else None
            summary = None
            if session is not None:
                summary = session.process_observation(
                    score,
                    coverage,
                    should_record=reference is not None,
                    bone_scores=bone_scores,
                    count=_parse_count(payload.get("count")),
                    loop_complete=bool(payload.get("loop_complete", False)),
                )
                state = session.mastery.state()
            else:
                state = None
            response: dict[str, Any] = {
                "type": "pose",
                "status": "success" if observation is not None else "no_pose_detected",
                "session_id": session_id or None,
                "score": score,
                "coverage": coverage,
                "bone_scores": bone_scores,
                "state": state,
                "speed": state["speed"] if state else None,
                "loop": summary.to_dict() if summary else None,
                "coaching": deterministic_coaching(
                    score,
                    bone_scores,
                    coverage=coverage,
                    mastered=bool(state and state["mastered"]),
                    preferred_bone=session.policy_focus_bone if session else None,
                ),
                **_comparison_payload(comparison),
            }
            if session is not None:
                response.update(session.learning_payload())
            if observation is not None:
                response.update(observation.to_dict())
            await websocket.send_json(response)
    except WebSocketDisconnect:
        return


def _mount_static_frontend() -> None:
    project_root = Path(__file__).resolve().parents[1]
    configured = os.getenv("TEMPO_FRONTEND_DIR")
    candidates = [Path(configured)] if configured else []
    candidates.extend(
        [
            project_root / "frontend" / "out",
            project_root / "frontend" / "dist",
            project_root / "frontend",
        ]
    )
    for candidate in candidates:
        if candidate.is_dir() and (candidate / "index.html").is_file():
            app.mount("/", StaticFiles(directory=str(candidate), html=True), name="frontend")
            break


# Mounted last so API and WebSocket routes keep priority.
_mount_static_frontend()
