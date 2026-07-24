"""Tolerant HTTP/WS input contracts for rapid frontend iteration."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TolerantModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class SessionCreate(TolerantModel):
    routine_url: str | None = None
    mode: str = "full"
    analysis_provider: str | None = None
    frame_data_urls: list[str] = Field(default_factory=list)


class ObservationRequest(TolerantModel):
    score: float | None = None
    coverage: float | None = None
    bone_scores: Any = None
    frame_base64: str | None = None
    frame: str | None = None
    reference_keypoints: list[Any] | None = None
    reference: list[Any] | None = None
    focus: str | None = None
    confidence_threshold: float = 0.35
    allow_mirror: bool = True
    count: int | str | None = None
    speed: float | None = None
    loop_complete: bool = False


class LoopCompleteRequest(TolerantModel):
    force: bool = False
