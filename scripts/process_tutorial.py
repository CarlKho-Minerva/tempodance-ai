#!/usr/bin/env python3
"""Download a tutorial, extract the lower coach pose, and package browser assets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import wave

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.pose_engine import PoseEngine


DEFAULT_URL = "https://www.youtube.com/shorts/jrUsvBKemBU"
DEFAULT_VIDEO_ID = "jrUsvBKemBU"


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


def extract_beats(source: Path, working_dir: Path) -> tuple[float, list[float]]:
    """Return an onset-derived tempo and beat grid without optional audio packages."""

    wav_path = working_dir / "analysis.wav"
    run([
        "ffmpeg", "-y", "-v", "error", "-i", str(source), "-vn",
        "-ac", "1", "-ar", "22050", "-c:a", "pcm_s16le", str(wav_path),
    ])
    with wave.open(str(wav_path), "rb") as audio_file:
        sample_rate = audio_file.getframerate()
        samples = np.frombuffer(audio_file.readframes(audio_file.getnframes()), np.int16).astype(np.float32) / 32768

    window_size = 2048
    hop_size = 256
    window = np.hanning(window_size)
    spectra = np.array([
        np.abs(np.fft.rfft(samples[start:start + window_size] * window))
        for start in range(0, len(samples) - window_size, hop_size)
    ])
    flux = np.maximum(0, np.diff(spectra, axis=0)).sum(axis=1)
    flux = np.maximum(0, (flux - np.median(flux)) / (np.std(flux) + 1e-9))
    feature_rate = sample_rate / hop_size
    candidates: list[tuple[float, float]] = []
    for bpm in np.arange(70.0, 181.0, 0.25):
        lag = round(feature_rate * 60 / bpm)
        score = float(np.dot(flux[lag:], flux[:-lag]) / max(1, len(flux) - lag))
        candidates.append((score, float(bpm)))
    raw_bpm = max(candidates)[1]
    bpm = round(raw_bpm / 2) * 2
    period = 60 / bpm
    feature_times = np.arange(len(flux)) / feature_rate
    offsets = np.arange(0, period, hop_size / sample_rate)
    duration = len(samples) / sample_rate
    offset = max(
        offsets,
        key=lambda candidate: float(np.interp(np.arange(candidate, duration, period), feature_times, flux).sum()),
    )
    beats = [round(float(value), 4) for value in np.arange(offset, duration, period)]
    return float(bpm), beats


def extract_motion(
    source: Path,
    destination: Path,
    *,
    model_path: str,
    sample_fps: float,
    crop_top_ratio: float,
    working_dir: Path,
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
    bpm, beats = extract_beats(source, working_dir)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps({
        "source": DEFAULT_URL,
        "video_id": DEFAULT_VIDEO_ID,
        "model": Path(model_path).name,
        "format": "COCO-17",
        "duration": round(duration, 4),
        "sample_fps": sample_fps,
        "crop_top_ratio": crop_top_ratio,
        "detected_bpm": bpm,
        "beats": beats,
        "poses": poses,
        "confidences": confidences,
    }, separators=(",", ":")))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--model", default="yolo11n-pose.pt")
    parser.add_argument("--sample-fps", type=float, default=30.0)
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
            working_dir=Path(temp_name),
        )
        print(f"Wrote {video_output} and {motion_output}")


if __name__ == "__main__":
    main()
