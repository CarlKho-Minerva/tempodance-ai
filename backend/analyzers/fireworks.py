"""Optional Fireworks routine analyzer.

Only a real ``FIREWORKS_API_KEY`` supplied through the environment should reach
this class.  Promotional redemption codes are not API credentials.
"""

from __future__ import annotations

import json
import os
from typing import Any, Sequence

import requests

from .base import (
    AnalyzerUnavailable,
    RoutineAnalysis,
    RoutineAnalyzer,
    RoutineSegment,
)


class FireworksAnalyzer(RoutineAnalyzer):
    def __init__(
        self,
        *,
        api_key: str,
        model: str | None = None,
        endpoint: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        if not api_key.strip():
            raise AnalyzerUnavailable("FIREWORKS_API_KEY is empty")
        self.api_key = api_key.strip()
        self.model = (
            model
            or os.getenv("FIREWORKS_MODEL")
            or "accounts/fireworks/models/kimi-k2p5"
        ).strip()
        base_url = os.getenv("FIREWORKS_BASE_URL", "").strip().rstrip("/")
        self.endpoint = (
            endpoint
            or os.getenv("FIREWORKS_API_URL")
            or (f"{base_url}/chat/completions" if base_url else None)
            or "https://api.fireworks.ai/inference/v1/chat/completions"
        )
        self.timeout_seconds = timeout_seconds

    def analyze(
        self,
        routine_url: str,
        mode: str,
        frame_data_urls: Sequence[str] = (),
    ) -> RoutineAnalysis:
        prompt = (
            "Create a concise dance-practice plan from these ordered keyframes. "
            "Return a JSON object with title, summary, and exactly four segments. "
            "Each segment needs count_start, count_end, focus (upper/lower/full), "
            "and instruction. Counts must cover 1-8. "
            f"Requested focus: {mode}. Source label: {routine_url or 'uploaded routine'}."
        )
        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        for frame in frame_data_urls[:8]:
            if isinstance(frame, str) and frame.startswith("data:image/"):
                content.append({"type": "image_url", "image_url": {"url": frame}})

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": content}],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }
        try:
            response = requests.post(
                self.endpoint,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            body = response.json()
            raw_content = body["choices"][0]["message"]["content"]
            parsed = self._parse_content(raw_content)
            return self._to_analysis(parsed)
        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
            raise AnalyzerUnavailable(f"Fireworks analysis failed: {exc}") from exc

    @staticmethod
    def _parse_content(content: Any) -> dict[str, Any]:
        if isinstance(content, list):
            content = "".join(
                str(item.get("text", ""))
                for item in content
                if isinstance(item, dict)
            )
        if not isinstance(content, str):
            raise ValueError("Fireworks response content is not text")
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.removeprefix("```json").removeprefix("```")
            cleaned = cleaned.removesuffix("```").strip()
        parsed = json.loads(cleaned)
        if not isinstance(parsed, dict):
            raise ValueError("Fireworks response is not a JSON object")
        return parsed

    @staticmethod
    def _to_analysis(data: dict[str, Any]) -> RoutineAnalysis:
        raw_segments = data.get("segments")
        if not isinstance(raw_segments, list) or not raw_segments:
            raise ValueError("Fireworks response has no segments")
        segments: list[RoutineSegment] = []
        for item in raw_segments[:8]:
            if not isinstance(item, dict):
                continue
            focus = str(item.get("focus", "full")).lower()
            if focus not in {"upper", "lower", "full"}:
                focus = "full"
            segments.append(
                RoutineSegment(
                    count_start=max(1, min(8, int(item.get("count_start", 1)))),
                    count_end=max(1, min(8, int(item.get("count_end", 8)))),
                    focus=focus,
                    instruction=str(item.get("instruction", "Match the reference shape."))[:300],
                )
            )
        if not segments:
            raise ValueError("Fireworks returned no valid segments")
        return RoutineAnalysis(
            provider="fireworks",
            title=str(data.get("title", "AI-assisted routine"))[:120],
            summary=str(data.get("summary", "Generated 8-count practice plan."))[:500],
            segments=tuple(segments),
        )
