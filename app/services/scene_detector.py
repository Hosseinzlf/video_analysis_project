import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple

from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger("scene_detector")


class SceneDetector:
    """
    Detects scene changes in a video by comparing consecutive frames.

    How it works:
    - Reads frames one by one
    - Converts each frame to HSV color space
    - Compares the histogram of each frame to the previous one
    - If the difference is above the threshold → new scene detected
    - Returns a list of (start_frame, end_frame) for each scene
    """

    def __init__(self, threshold: float = None):
        # threshold controls sensitivity:
        # lower  = more sensitive (detects small changes)
        # higher = less sensitive (only detects big changes)
        self.threshold = threshold or settings.scene_threshold

    # ──────────────────────────────────────────────────────────────
    # 1. DETECT SCENES
    # ──────────────────────────────────────────────────────────────
    def detect_scenes(self, video_path: str) -> List[Tuple[int, int]]:
        """
        Analyze the video and find all scene boundaries.
        Returns: list of (start_frame, end_frame) tuples
        Example: [(0, 45), (46, 120), (121, 200)]
        """
        try:
            logger.info(f"Starting scene detection: {video_path}")
            logger.info(f"Threshold: {self.threshold}")

            cap         = cv2.VideoCapture(video_path)
            total       = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            scenes      = []
            scene_start = 0
            prev_hist   = None

            for frame_num in range(total):
                ret, frame = cap.read()
                if not ret:
                    break

                # Calculate histogram for this frame
                curr_hist = self._get_histogram(frame)

                if prev_hist is not None:
                    # Compare this frame's histogram to the previous one
                    diff = self._compare_histograms(prev_hist, curr_hist)

                    # If difference is big enough → scene change detected
                    if diff > self.threshold:
                        # Only save scene if it's long enough
                        if (frame_num - scene_start) >= settings.min_scene_length:
                            scenes.append((scene_start, frame_num - 1))
                            scene_start = frame_num
                            logger.debug(
                                f"Scene change at frame {frame_num} "
                                f"(diff={diff:.2f})"
                            )

                prev_hist = curr_hist

            # Don't forget the last scene
            if scene_start < total - 1:
                scenes.append((scene_start, total - 1))

            cap.release()

            logger.info(f"Detected {len(scenes)} scenes")
            return scenes

        except Exception as e:
            logger.error(f"Scene detection failed: {e}")
            raise Exception(f"Scene detection failed: {e}")

    # ──────────────────────────────────────────────────────────────
    # 2. GET KEYFRAME FOR EACH SCENE
    # ──────────────────────────────────────────────────────────────
    def get_scene_keyframes(self, scenes: List[Tuple[int, int]]) -> List[int]:
        """
        For each scene, return the middle frame number.
        Middle frame is the most representative frame of a scene.

        Example:
            Scene (0, 44)   → keyframe = 22
            Scene (45, 120) → keyframe = 82
        """
        keyframes = []
        for start, end in scenes:
            middle = (start + end) // 2
            keyframes.append(middle)

        logger.info(f"Generated {len(keyframes)} keyframes")
        return keyframes

    # ──────────────────────────────────────────────────────────────
    # 3. HISTOGRAM HELPERS (internal)
    # ──────────────────────────────────────────────────────────────
    def _get_histogram(self, frame: np.ndarray) -> np.ndarray:
        """
        Convert frame to HSV and calculate its color histogram.
        HSV is better than RGB for scene comparison because it
        separates color (Hue) from brightness (Value).
        """
        hsv  = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist(
            [hsv],          # image
            [0, 1],         # channels: Hue + Saturation
            None,           # no mask
            [50, 60],       # bins
            [0, 180, 0, 256] # ranges
        )
        # Normalize so videos with different brightness are comparable
        cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
        return hist

    def _compare_histograms(
        self,
        hist1: np.ndarray,
        hist2: np.ndarray
    ) -> float:
        """
        Compare two histograms and return a difference score.
        Uses Chi-Square method — higher score = more different.
        Score of 0.0 = identical frames
        Score > threshold = scene change
        """
        score = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CHISQR)
        return score