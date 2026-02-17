"""
STEP 3 VALIDATION SCRIPT
Location: video-analysis-api/step3_validation.py

Usage (run from video-analysis-api directory, using your conda env):

  In terminal (activate your env first, then run):
    conda activate video-analysis-api
    python step3_validation.py uploads/test_video.mp4

  In Cursor: select the "video-analysis-api" Python interpreter (Python 3.11)
  so that Run / Run Python File uses that env.
"""

import sys
import os
from pathlib import Path

# Ensure we can import app.* when run from video-analysis-api
_script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(_script_dir))
os.chdir(_script_dir)

# Unbuffered output so you see progress when run from CLI
def _out(*args, **kwargs):
    kwargs.setdefault("flush", True)
    print(*args, **kwargs)

print("Step 3 validation starting...", flush=True)

PASS = "✅"
FAIL = "❌"
results = []

def check(label, fn):
    try:
        fn()
        _out(f"  {PASS}  {label}")
        results.append((label, True))
    except Exception as e:
        _out(f"  {FAIL}  {label}")
        _out(f"       └─ {e}")
        results.append((label, False))


_out("\n" + "=" * 55)
_out("  STEP 3 VALIDATION: Scene Detection")
_out("=" * 55)

# ── Get video path ────────────────────────────────────────────
video_path = sys.argv[1] if len(sys.argv) > 1 else None

if not video_path:
    _out("\n  No video path provided.")
    _out("  Usage: python step3_validation.py your_video.mp4\n")
    sys.exit(1)

# Resolve path: try as-is, then relative to script directory
video_path = Path(video_path)
if not video_path.is_absolute():
    video_path = (_script_dir / video_path).resolve()
else:
    video_path = video_path.resolve()

if not video_path.exists():
    _out(f"\n  {FAIL} Video file not found: {video_path}")
    sys.exit(1)

video_path = str(video_path)
_out(f"\n  Testing with: {video_path}\n")


# ── 1. Import SceneDetector ───────────────────────────────────
_out("[1] Checking imports...")

def import_scene_detector():
    from app.services.scene_detector import SceneDetector

def import_updated_processor():
    from app.services.video_processor import VideoProcessor
    p = VideoProcessor()
    # confirm new method exists
    assert hasattr(p, "extract_frames_smart")
    assert hasattr(p, "extract_frames_from_scenes")

check("Import: app.services.scene_detector",        import_scene_detector)
check("Import: VideoProcessor (updated with smart)", import_updated_processor)


# ── 2. Create SceneDetector ───────────────────────────────────
_out("\n[2] Creating SceneDetector instance...")

detector = None

def create_detector():
    global detector
    from app.services.scene_detector import SceneDetector
    detector = SceneDetector()
    assert detector is not None
    assert detector.threshold > 0

check("SceneDetector created", create_detector)


# ── 3. Detect scenes ──────────────────────────────────────────
_out("\n[3] Running scene detection...")

scenes = []

def detect_scenes():
    global scenes
    scenes = detector.detect_scenes(video_path)
    assert isinstance(scenes, list)

    # Each scene must be a (start, end) tuple
    for s in scenes:
        assert len(s) == 2, "Scene must be (start, end) tuple"
        assert s[0] <= s[1],  "Start frame must be <= end frame"
        assert s[0] >= 0,     "Start frame must be >= 0"

    _out(f"\n       Scenes detected : {len(scenes)}")
    for i, (start, end) in enumerate(scenes):
        _out(f"       Scene {i+1}: frames {start} → {end}  ({end - start} frames long)")

check("Scene detection ran successfully", detect_scenes)


# ── 4. Get keyframes ──────────────────────────────────────────
_out("\n[4] Getting keyframes from scenes...")

keyframes = []

def get_keyframes():
    global keyframes
    if len(scenes) == 0:
        _out("       No scenes to get keyframes from — skipping")
        return
    keyframes = detector.get_scene_keyframes(scenes)
    assert len(keyframes) == len(scenes)
    _out(f"\n       Keyframe numbers: {keyframes}")

check("Keyframes generated", get_keyframes)


# ── 5. Smart extraction ───────────────────────────────────────
_out("\n[5] Testing smart frame extraction...")

smart_frames = []

def smart_extract():
    global smart_frames
    from app.services.video_processor import VideoProcessor
    processor    = VideoProcessor()
    smart_frames = processor.extract_frames_smart(video_path)

    assert len(smart_frames) > 0, "No frames extracted"
    for p in smart_frames:
        assert Path(p).exists(),          f"Frame missing: {p}"
        assert Path(p).stat().st_size > 0, f"Frame is empty: {p}"

    _out(f"\n       Frames extracted : {len(smart_frames)}")
    for p in smart_frames:
        size_kb = Path(p).stat().st_size // 1024
        _out(f"       • {Path(p).name}  ({size_kb} KB)")

check("Smart frame extraction works", smart_extract)


# ── 6. Cleanup ────────────────────────────────────────────────
_out("\n[6] Cleaning up...")

def cleanup():
    from app.services.video_processor import VideoProcessor
    processor = VideoProcessor()
    processor.cleanup_frames(smart_frames)
    for p in smart_frames:
        assert not Path(p).exists(), f"Frame not deleted: {p}"

check("Temp frames cleaned up", cleanup)


# ── Summary ───────────────────────────────────────────────────
_out("\n" + "=" * 55)
passed = sum(1 for _, ok in results if ok)
failed = sum(1 for _, ok in results if not ok)

_out(f"  Result: {passed}/{len(results)} checks passed\n")

if failed == 0:
    _out(f"  {PASS} Step 3 complete! Ready for Step 4 (API Routes).")
else:
    _out(f"  {FAIL} {failed} check(s) failed.\n")
    _out("  Common fixes:")
    _out("    'No module scenedetect' → pip install scenedetect[opencv]")
    _out("    'No scenes detected'    → try lowering SCENE_THRESHOLD in .env")

_out("=" * 55 + "\n")
sys.exit(0 if failed == 0 else 1)
