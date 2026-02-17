"""
STEP 2 VALIDATION SCRIPT
Location: video-analysis-api/step2_validation.py

Usage (run from video-analysis-api directory, using your conda env):

  In terminal (activate your env first, then run):
    conda activate video-analysis-api
    python step2_validation.py uploads/test_video.mp4

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

print("Step 2 validation starting...", flush=True)

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
_out("  STEP 2 VALIDATION: Video Processor")
_out("=" * 55)

# ── Get video path from args ───────────────────────────────────
video_path = sys.argv[1] if len(sys.argv) > 1 else None

if not video_path:
    _out("\n  No video path provided.")
    _out("  Usage: python step2_validation.py your_video.mp4\n")
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


# ── 1. Import check ───────────────────────────────────────────
_out("[1] Checking imports...")

def import_processor():
    from app.services.video_processor import VideoProcessor

check("Import: app.services.video_processor", import_processor)


# ── 2. Instantiation ──────────────────────────────────────────
_out("\n[2] Creating VideoProcessor instance...")

processor = None

def create_instance():
    global processor
    from app.services.video_processor import VideoProcessor
    processor = VideoProcessor()
    assert processor is not None

check("VideoProcessor created", create_instance)


# ── 3. Validate video ─────────────────────────────────────────
_out("\n[3] Validating video file...")

def validate():
    result = processor.validate_video(video_path)
    assert result is True

check("Video is valid", validate)


# ── 4. Get metadata ───────────────────────────────────────────
_out("\n[4] Reading video metadata...")

info = {}

def get_metadata():
    global info
    info = processor.get_video_info(video_path)
    assert "duration"     in info
    assert "width"        in info
    assert "height"       in info
    assert "fps"          in info
    assert "total_frames" in info
    assert info["duration"] > 0
    assert info["width"]    > 0
    assert info["height"]   > 0
    _out(f"\n       Duration    : {info['duration']:.2f} seconds")
    _out(f"       Resolution  : {info['width']} x {info['height']}")
    _out(f"       FPS         : {info['fps']:.2f}")
    _out(f"       Total frames: {info['total_frames']}")
    _out(f"       Format      : {info['format']}")

check("Metadata extracted", get_metadata)


# ── 5. Extract frames ─────────────────────────────────────────
_out("\n[5] Extracting frames from video...")

frame_paths = []

def extract_frames():
    global frame_paths
    frame_paths = processor.extract_frames_uniform(video_path, num_frames=5)
    assert len(frame_paths) > 0, "No frames were extracted"
    for p in frame_paths:
        assert Path(p).exists(), f"Frame file missing: {p}"
        assert Path(p).suffix == ".jpg"
        assert Path(p).stat().st_size > 0, f"Frame file is empty: {p}"
    _out(f"\n       Extracted {len(frame_paths)} frames:")
    for p in frame_paths:
        size_kb = Path(p).stat().st_size // 1024
        _out(f"       • {Path(p).name}  ({size_kb} KB)")

check("Frames extracted successfully", extract_frames)


# ── 6. Cleanup ────────────────────────────────────────────────
_out("\n[6] Cleaning up temp frames...")

def cleanup():
    processor.cleanup_frames(frame_paths)
    for p in frame_paths:
        assert not Path(p).exists(), f"Frame was not deleted: {p}"

check("Temp frames cleaned up", cleanup)


# ── Summary ───────────────────────────────────────────────────
_out("\n" + "=" * 55)
passed = sum(1 for _, ok in results if ok)
failed = sum(1 for _, ok in results if not ok)

_out(f"  Result: {passed}/{len(results)} checks passed\n")

if failed == 0:
    _out(f"  {PASS} Step 2 complete! Ready for Step 3 (Scene Detection).")
else:
    _out(f"  {FAIL} {failed} check(s) failed. Fix the issues above.")
    _out("\n  Common fixes:")
    _out("    'ffmpeg not found'  → install ffmpeg on your system")
    _out("    'cv2 not found'     → pip install opencv-python")
    _out("    'No frames'         → check your video file is not corrupted")

_out("=" * 55 + "\n")
sys.exit(0 if failed == 0 else 1)
