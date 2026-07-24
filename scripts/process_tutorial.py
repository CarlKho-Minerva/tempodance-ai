#!/usr/bin/env python3
"""Download a tutorial, extract the lower coach pose, and package browser assets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.pose_engine import PoseEngine


DEFAULT_URL = "https://www.youtube.com/shorts/W0N9pOGTgZM"
DEFAULT_VIDEO_ID = "W0N9pOGTgZM"


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def download(url: str, target_dir: Path) -> Path:
    output = target_dir / "source.%(ext)s"
    run([
        "yt-dlp",
        "--no-playlist",
        "-f",
        "bv*[height<=720]+ba/b[height<=720]",
        "--merge-output-format",
        "mp4",
        "-o",
        str(output),
        url,
    ])
    matches = sorted(target_dir.glob("source.*"))
    if not matches:
        raise RuntimeError("yt-dlp did not produce a source video")
    return matches[0]


def transcode_for_browser(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    run([
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-i",
        str(source),
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        str(destination),
    ])


def extract_motion(
    source: Path,
    destination: Path,
    *,
    model_path: str,
    sample_fps: float,
    crop_top_ratio: float,
) -> None:
    capture = cv2.VideoCapture(str(source))
    source_fps = float(capture.get(cv2.CAP_PROP_FPS))
    frame_count = float(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / source_fps
    engine = PoseEngine(model_name=model_path)
    poses: list[list[list[float]] | None] = []
    confidences: list[float] = []
    sample_count = int(duration * sample_fps) + 1

    for sample_index in range(sample_count):
        time_seconds = sample_index / sample_fps
        capture.set(cv2.CAP_PROP_POS_MSEC, time_seconds * 1000)
        ok, frame = capture.read()
        if not ok:
            break
        height, width = frame.shape[:2]
        crop_top = round(height * crop_top_ratio)
        observation = engine.extract(frame[crop_top:])
        if observation is None:
            poses.append(None)
            confidences.append(0.0)
            continue
        poses.append([
            [round(point.x / width, 4), round((point.y + crop_top) / height, 4)]
            for point in observation.keypoints
        ])
        confidences.append(round(observation.person_confidence, 3))

    capture.release()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps({
        "source": DEFAULT_URL,
        "video_id": DEFAULT_VIDEO_ID,
        "model": Path(model_path).name,
        "format": "COCO-17",
        "duration": round(duration, 4),
        "sample_fps": sample_fps,
        "crop_top_ratio": crop_top_ratio,
        "poses": poses,
        "confidences": confidences,
    }, separators=(",", ":")))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--model", default="yolo11n-pose.pt")
    parser.add_argument("--sample-fps", type=float, default=10.0)
    parser.add_argument("--crop-top-ratio", type=float, default=205 / 640)
    parser.add_argument("--output-dir", type=Path, default=Path("frontend/assets"))
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="tempodance-tutorial-") as temp_name:
        source = args.input or download(args.url, Path(temp_name))
        video_output = args.output_dir / f"tutorial-{DEFAULT_VIDEO_ID}.mp4"
        motion_output = args.output_dir / f"tutorial-{DEFAULT_VIDEO_ID}-pose.json"
        transcode_for_browser(source, video_output)
        extract_motion(
            source,
            motion_output,
            model_path=args.model,
            sample_fps=args.sample_fps,
            crop_top_ratio=args.crop_top_ratio,
        )
        print(f"Wrote {video_output} and {motion_output}")


if __name__ == "__main__":
    main()
