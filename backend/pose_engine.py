"""Lazy Ultralytics pose inference and browser-frame decoding."""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
import os
import threading
import time
from typing import Any

from .scoring import Keypoint


class PoseEngineError(RuntimeError):
    """Raised when a frame cannot be decoded or pose inference cannot run."""


@dataclass(frozen=True, slots=True)
class PoseObservation:
    keypoints: tuple[Keypoint, ...]
    person_confidence: float
    device: str
    frame_width: int
    frame_height: int
    inference_ms: float

    def to_dict(self) -> dict[str, Any]:
        return {
            # Array form is compact and directly accepted by compare_poses.
            "keypoints": [
                [point.x, point.y, point.confidence] for point in self.keypoints
            ],
            "person_confidence": self.person_confidence,
            "device": self.device,
            "width": self.frame_width,
            "height": self.frame_height,
            "frame_width": self.frame_width,
            "frame_height": self.frame_height,
            "inference_ms": round(self.inference_ms, 2),
        }


def decode_image_data(data: str, *, max_bytes: int = 6_000_000) -> Any:
    """Decode a base64/data-URL browser frame into an OpenCV BGR array."""

    if not isinstance(data, str) or not data.strip():
        raise PoseEngineError("Frame must be a non-empty base64 string")
    payload = data.split(",", 1)[1] if "," in data else data
    try:
        raw = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise PoseEngineError("Frame is not valid base64") from exc
    if not raw:
        raise PoseEngineError("Decoded frame is empty")
    if len(raw) > max_bytes:
        raise PoseEngineError(f"Decoded frame exceeds {max_bytes} bytes")

    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise PoseEngineError("OpenCV and NumPy are required to decode frames") from exc
    image = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise PoseEngineError("Decoded payload is not a supported image")
    return image


class PoseEngine:
    """Thread-safe, lazy wrapper around an Ultralytics COCO-17 pose model.

    Construction and API import do not load Torch, download model weights, or
    allocate GPU memory.  The first :meth:`extract` call performs that work.
    Set ``TEMPO_POSE_MODEL`` to a local weight path for a fully offline demo.
    """

    def __init__(self, model_name: str | None = None, device: str | None = None) -> None:
        self.model_name = model_name or os.getenv("TEMPO_POSE_MODEL") or "yolo11n-pose.pt"
        self.requested_device = device or os.getenv("TEMPO_DEVICE") or "auto"
        self._model: Any = None
        self._device: str | None = None
        self._load_lock = threading.Lock()
        self._inference_lock = threading.Lock()

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def device(self) -> str:
        return self._device or self.requested_device

    def status(self) -> dict[str, Any]:
        return {
            "loaded": self.is_loaded,
            "model": self.model_name,
            "device": self.device,
            "lazy": True,
        }

    def _resolve_device(self, torch: Any) -> str:
        requested = self.requested_device.lower()
        if requested != "auto":
            return requested
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        with self._load_lock:
            if self._model is not None:
                return
            try:
                import torch
                from ultralytics import YOLO

                device = self._resolve_device(torch)
                model = YOLO(self.model_name)
            except Exception as exc:  # model loading has several provider errors
                raise PoseEngineError(f"Unable to load pose model: {exc}") from exc
            self._device = device
            self._model = model

    def extract(self, frame: Any) -> PoseObservation | None:
        """Return the most confident person's 17 keypoints, or ``None``."""

        started = time.perf_counter()
        self._ensure_loaded()
        try:
            with self._inference_lock:
                results = self._model.predict(
                    source=frame,
                    device=self._device,
                    verbose=False,
                    max_det=4,
                )
        except Exception as exc:
            raise PoseEngineError(f"Pose inference failed: {exc}") from exc
        if not results:
            return None
        keypoints = getattr(results[0], "keypoints", None)
        if keypoints is None or keypoints.xy is None or len(keypoints.xy) == 0:
            return None

        confidences = getattr(keypoints, "conf", None)
        person_index = 0
        if confidences is not None and len(confidences) > 1:
            means = confidences.mean(dim=1)
            person_index = int(means.argmax().item())
        xy = keypoints.xy[person_index].detach().cpu().tolist()
        if confidences is None:
            conf = [1.0] * len(xy)
        else:
            conf = confidences[person_index].detach().cpu().tolist()
        if len(xy) < 17:
            return None
        points = tuple(
            Keypoint(float(coords[0]), float(coords[1]), float(conf[index]))
            for index, coords in enumerate(xy[:17])
        )
        person_confidence = sum(point.confidence for point in points) / len(points)
        shape = getattr(frame, "shape", ())
        frame_height = int(shape[0]) if len(shape) >= 2 else 0
        frame_width = int(shape[1]) if len(shape) >= 2 else 0
        inference_ms = (time.perf_counter() - started) * 1000.0
        return PoseObservation(
            points,
            person_confidence,
            self.device,
            frame_width,
            frame_height,
            inference_ms,
        )
