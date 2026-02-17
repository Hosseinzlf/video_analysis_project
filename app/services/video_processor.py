import cv2
import os
import uuid
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
import ffmpeg

from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger("video_processor")


class VideoProcessor:
    """
    Handles all video file operations:
    - Validate the video file
    - Extract metadata (duration, fps, size)
    - Extract frames as jpg images (uniform or smart)
    - Clean up temporary files
    """

    def __init__(self, temp_dir: str = None):
        self.temp_dir = Path(temp_dir or settings.temp_dir)
        self.temp_dir.mkdir(exist_ok=True)

        from app.services.scene_detector import SceneDetector
        self.scene_detector = SceneDetector()

    def get_video_info(self, video_path: str) -> Dict:
        try:
            logger.info(f"Reading metadata for: {video_path}")
            probe        = ffmpeg.probe(video_path)
            video_stream = next(s for s in probe["streams"] if s["codec_type"] == "video")
            duration     = float(probe["format"]["duration"])
            width        = int(video_stream["width"])
            height       = int(video_stream["height"])
            fps_str      = video_stream["r_frame_rate"]
            num, den     = fps_str.split("/")
            fps          = float(num) / float(den)
            total_frames = int(video_stream.get("nb_frames", 0))
            if total_frames == 0:
                total_frames = int(duration * fps)
            info = {"duration": duration, "width": width, "height": height,
                    "fps": fps, "total_frames": total_frames,
                    "format": probe["format"]["format_name"]}
            logger.info(f"Metadata: {info}")
            return info
        except Exception as e:
            logger.error(f"Failed to read metadata: {e}")
            raise Exception(f"Could not read video info: {e}")

    def validate_video(self, video_path: str) -> bool:
        try:
            logger.info(f"Validating video: {video_path}")
            if not Path(video_path).exists():
                raise FileNotFoundError(f"File not found: {video_path}")
            info = self.get_video_info(video_path)
            if info["duration"] > settings.max_video_duration:
                raise ValueError(f"Video too long: {info['duration']:.0f}s")
            if info["total_frames"] < 1:
                raise ValueError("Video has no frames")
            logger.info("Video validation passed")
            return True
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            raise

    def extract_frames_uniform(self, video_path: str, num_frames: int) -> List[str]:
        try:
            logger.info(f"Extracting {num_frames} frames uniformly")
            frame_dir    = self.temp_dir / str(uuid.uuid4())
            frame_dir.mkdir(exist_ok=True)
            cap          = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames <= num_frames:
                frame_indices = list(range(total_frames))
            else:
                frame_indices = [int(i) for i in np.linspace(0, total_frames - 1, num_frames)]
            extracted = []
            for idx, frame_num in enumerate(frame_indices):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                if ret:
                    frame      = self._resize_frame(frame)
                    frame_path = frame_dir / f"frame_{idx:03d}.jpg"
                    cv2.imwrite(str(frame_path), frame, [cv2.IMWRITE_JPEG_QUALITY, settings.frame_quality])
                    extracted.append(str(frame_path))
            cap.release()
            logger.info(f"Extracted {len(extracted)} frames uniformly")
            return extracted
        except Exception as e:
            logger.error(f"Uniform extraction failed: {e}")
            raise

    def extract_frames_from_scenes(self, video_path: str, scenes: List[Tuple[int, int]]) -> List[str]:
        try:
            logger.info(f"Extracting frames from {len(scenes)} scenes")
            frame_dir = self.temp_dir / str(uuid.uuid4())
            frame_dir.mkdir(exist_ok=True)
            keyframes = self.scene_detector.get_scene_keyframes(scenes)
            cap       = cv2.VideoCapture(video_path)
            extracted = []
            for idx, frame_num in enumerate(keyframes):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                if ret:
                    frame      = self._resize_frame(frame)
                    frame_path = frame_dir / f"scene_{idx:03d}.jpg"
                    cv2.imwrite(str(frame_path), frame, [cv2.IMWRITE_JPEG_QUALITY, settings.frame_quality])
                    extracted.append(str(frame_path))
            cap.release()
            logger.info(f"Extracted {len(extracted)} scene frames")
            return extracted
        except Exception as e:
            logger.error(f"Scene frame extraction failed: {e}")
            raise

    def extract_frames_smart(self, video_path: str) -> List[str]:
        try:
            logger.info("Starting smart frame extraction")
            try:
                scenes = self.scene_detector.detect_scenes(video_path)
                logger.info(f"Found {len(scenes)} scenes")
                if len(scenes) == 0:
                    logger.warning("No scenes found, using uniform sampling")
                    return self.extract_frames_uniform(video_path, settings.default_frames)
                if len(scenes) > settings.max_frames:
                    logger.info(f"Too many scenes ({len(scenes)}), sampling down to {settings.max_frames}")
                    indices = np.linspace(0, len(scenes) - 1, settings.max_frames, dtype=int)
                    scenes  = [scenes[i] for i in indices]
                elif len(scenes) < settings.min_frames:
                    logger.info(f"Too few scenes ({len(scenes)}), adding uniform frames")
                    scene_frames   = self.extract_frames_from_scenes(video_path, scenes)
                    needed         = settings.min_frames - len(scene_frames)
                    uniform_frames = self.extract_frames_uniform(video_path, needed)
                    return scene_frames + uniform_frames
                return self.extract_frames_from_scenes(video_path, scenes)
            except Exception as scene_error:
                logger.warning(f"Scene detection failed ({scene_error}), falling back to uniform")
                return self.extract_frames_uniform(video_path, settings.default_frames)
        except Exception as e:
            logger.error(f"Smart extraction failed: {e}")
            raise

    def _resize_frame(self, frame: np.ndarray) -> np.ndarray:
        height, width = frame.shape[:2]
        max_dim       = settings.max_frame_dimension
        if max(height, width) > max_dim:
            if width >= height:
                new_w, new_h = max_dim, int(height * (max_dim / width))
            else:
                new_h, new_w = max_dim, int(width * (max_dim / height))
            frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
        return frame

    def cleanup_frames(self, frame_paths: List[str]):
        for frame_path in frame_paths:
            try:
                os.remove(frame_path)
            except Exception as e:
                logger.warning(f"Could not delete {frame_path}: {e}")
        if frame_paths:
            try:
                parent = Path(frame_paths[0]).parent
                if not any(parent.iterdir()):
                    parent.rmdir()
                    logger.info(f"Removed temp folder: {parent}")
            except Exception as e:
                logger.warning(f"Could not remove temp folder: {e}")