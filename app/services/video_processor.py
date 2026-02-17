import cv2
import json
import os
import subprocess
import uuid
import numpy as np
from pathlib import Path
from typing import List, Dict, Any

from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger("video_processor")

# Optional: use ffmpeg-python's probe if available (correct package is ffmpeg-python, not ffmpeg)
def _probe_with_ffmpeg_lib(video_path: str) -> Any:
    import ffmpeg
    if not hasattr(ffmpeg, "probe"):
        raise AttributeError("ffmpeg module has no 'probe' (install ffmpeg-python, not ffmpeg)")
    return ffmpeg.probe(video_path, cmd=settings.ffprobe_path)


def _probe_via_subprocess(video_path: str) -> Any:
    """Run ffprobe directly. Use when ffmpeg.probe is missing or fails."""
    cmd = [
        settings.ffprobe_path,
        "-show_format",
        "-show_streams",
        "-of", "json",
        "-v", "quiet",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or f"ffprobe failed: {result.returncode}")
    return json.loads(result.stdout)


class VideoProcessor:
    """
    Handles all video file operations:
    - Validate the video file
    - Extract metadata (duration, fps, size)
    - Extract frames as jpg images
    - Clean up temporary files
    """

    def __init__(self, temp_dir: str = ""):
        self.temp_dir = Path(temp_dir or settings.temp_dir)
        self.temp_dir.mkdir(exist_ok=True)

    # ──────────────────────────────────────────────────────────────
    # 1. GET VIDEO METADATA
    # ──────────────────────────────────────────────────────────────
    def get_video_info(self, video_path: str) -> Dict:
        """
        Read video metadata using ffprobe.
        Returns: duration, width, height, fps, total_frames, format
        """
        try:
            logger.info(f"Reading metadata for: {video_path}")

            # Prefer ffmpeg-python's probe; fall back to subprocess if wrong package or ffprobe not on PATH
            try:
                probe = _probe_with_ffmpeg_lib(video_path)
            except (AttributeError, FileNotFoundError, OSError):
                probe = _probe_via_subprocess(video_path)

            # Find the video stream inside the file
            video_stream = next(
                s for s in probe["streams"] if s["codec_type"] == "video"
            )

            duration = float(probe["format"]["duration"])
            width = int(video_stream["width"])
            height = int(video_stream["height"])

            # fps: fraction string e.g. "30/1" or "25/1", sometimes just "30"
            fps_str = video_stream.get("r_frame_rate", "30/1")
            if "/" in str(fps_str):
                num, den = fps_str.split("/", 1)
                fps = float(num) / float(den) if float(den) else 30.0
            else:
                fps = float(fps_str) if fps_str else 30.0

            # total frames — use nb_frames if present, otherwise calculate
            total_frames = int(video_stream.get("nb_frames", 0))
            if total_frames == 0:
                total_frames = int(duration * fps)

            info = {
                "duration": duration,
                "width": width,
                "height": height,
                "fps": fps,
                "total_frames": total_frames,
                "format": probe["format"]["format_name"],
            }

            logger.info(f"Metadata: {info}")
            return info

        except Exception as e:
            logger.error(f"Failed to read metadata: {e}")
            raise Exception(f"Could not read video info: {e}")

    # ──────────────────────────────────────────────────────────────
    # 2. VALIDATE VIDEO
    # ──────────────────────────────────────────────────────────────
    def validate_video(self, video_path: str) -> bool:
        """
        Check the video is usable before we start processing.
        Raises an error if something is wrong.
        """
        try:
            logger.info(f"Validating video: {video_path}")

            # Does the file exist?
            if not Path(video_path).exists():
                raise FileNotFoundError(f"File not found: {video_path}")

            # Can we read the metadata?
            info = self.get_video_info(video_path)

            # Is it too long?
            if info["duration"] > settings.max_video_duration:
                raise ValueError(
                    f"Video too long: {info['duration']:.0f}s "
                    f"(max {settings.max_video_duration}s)"
                )

            # Does it have frames?
            if info["total_frames"] < 1:
                raise ValueError("Video has no frames")

            logger.info("Video validation passed ✅")
            return True

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            raise

    # ──────────────────────────────────────────────────────────────
    # 3. EXTRACT FRAMES UNIFORMLY
    # ──────────────────────────────────────────────────────────────
    def extract_frames_uniform(self, video_path: str, num_frames: int) -> List[str]:
        """
        Extract N frames spread evenly across the video.
        Example: 10 frames from a 100-frame video = every 10th frame.
        Returns: list of saved jpg file paths
        """
        try:
            logger.info(f"Extracting {num_frames} frames uniformly")

            # Create a unique folder for this video's frames
            frame_dir = self.temp_dir / str(uuid.uuid4())
            frame_dir.mkdir(exist_ok=True)

            cap          = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # Calculate which frame numbers to extract
            if total_frames <= num_frames:
                # Video has fewer frames than requested — take all of them
                frame_indices = list(range(total_frames))
            else:
                # Spread evenly using linspace
                frame_indices = [
                    int(i) for i in np.linspace(0, total_frames - 1, num_frames)
                ]

            extracted = []

            for idx, frame_num in enumerate(frame_indices):
                # Jump to the frame
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()

                if ret:
                    frame = self._resize_frame(frame)
                    frame_path = frame_dir / f"frame_{idx:03d}.jpg"
                    cv2.imwrite(
                        str(frame_path),
                        frame,
                        [cv2.IMWRITE_JPEG_QUALITY, settings.frame_quality],
                    )
                    extracted.append(str(frame_path))

            cap.release()
            logger.info(f"Extracted {len(extracted)} frames")
            return extracted

        except Exception as e:
            logger.error(f"Frame extraction failed: {e}")
            raise

    # ──────────────────────────────────────────────────────────────
    # 4. RESIZE FRAME (helper)
    # ──────────────────────────────────────────────────────────────
    def _resize_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Shrink a frame if it's larger than max_frame_dimension.
        Keeps the aspect ratio intact.
        """
        height, width = frame.shape[:2]
        max_dim       = settings.max_frame_dimension

        if max(height, width) > max_dim:
            if width >= height:
                new_w = max_dim
                new_h = int(height * (max_dim / width))
            else:
                new_h = max_dim
                new_w = int(width * (max_dim / height))

            frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
            logger.debug(f"Resized frame {width}x{height} → {new_w}x{new_h}")

        return frame

    # ──────────────────────────────────────────────────────────────
    # 5. CLEANUP
    # ──────────────────────────────────────────────────────────────
    def cleanup_frames(self, frame_paths: List[str]):
        """
        Delete extracted jpg frames from disk after they've been analyzed.
        """
        for frame_path in frame_paths:
            try:
                os.remove(frame_path)
            except Exception as e:
                logger.warning(f"Could not delete frame {frame_path}: {e}")

        # Remove the parent folder if it's now empty
        if frame_paths:
            try:
                parent = Path(frame_paths[0]).parent
                if not any(parent.iterdir()):
                    parent.rmdir()
                    logger.info(f"Removed temp folder: {parent}")
            except Exception as e:
                logger.warning(f"Could not remove temp folder: {e}")