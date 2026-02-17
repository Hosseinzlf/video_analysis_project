"""
STEP 1 VALIDATION SCRIPT
Location: video-analysis-api/step1_validate.py

Run this after completing Step 1 setup:
    python step1_validate.py
"""

import sys
from pathlib import Path

PASS = "✅"
FAIL = "❌"

results = []

def check(label: str, fn):
    try:
        fn()
        print(f"  {PASS}  {label}")
        results.append((label, True))
    except Exception as e:
        print(f"  {FAIL}  {label}")
        print(f"       └─ {e}")
        results.append((label, False))


# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("  STEP 1 VALIDATION: Project Structure & Dependencies")
print("=" * 55)


# ── 1. Folder structure ───────────────────────────────────────
print("\n[1] Checking folder structure...")

REQUIRED_DIRS = [
    "app",
    "app/api",
    "app/core",
    "app/services",
    "app/models",
    "app/utils",
    "uploads",
    "outputs",
    "temp",
    "logs",
]

for d in REQUIRED_DIRS:
    check(f"Directory: {d}", lambda d=d: (_ for _ in ()).throw(
        FileNotFoundError(f"Missing folder: {d}")) if not Path(d).exists() else None)


# ── 2. Required files ─────────────────────────────────────────
print("\n[2] Checking required files...")

REQUIRED_FILES = [
    "requirements.txt",
    ".env",
    "app/__init__.py",
    "app/api/__init__.py",
    "app/core/__init__.py",
    "app/services/__init__.py",
    "app/models/__init__.py",
    "app/utils/__init__.py",
    "app/core/config.py",
    "app/utils/logger.py",
    "app/models/schemas.py",
]

for f in REQUIRED_FILES:
    check(f"File: {f}", lambda f=f: (_ for _ in ()).throw(
        FileNotFoundError(f"Missing file: {f}")) if not Path(f).exists() else None)


# ── 3. Python version ─────────────────────────────────────────
print("\n[3] Checking Python version...")

def check_python():
    major, minor = sys.version_info[:2]
    if major < 3 or (major == 3 and minor < 9):
        raise RuntimeError(f"Python 3.9+ required. You have: {major}.{minor}")
    print(f"       Python {major}.{minor} ✓")

check("Python >= 3.9", check_python)


# ── 4. Installed packages ─────────────────────────────────────
print("\n[4] Checking installed packages...")

PACKAGES = {
    "fastapi":           "fastapi",
    "uvicorn":           "uvicorn",
    "python-multipart":  "multipart",
    "opencv-python":     "cv2",
    "scenedetect":       "scenedetect",
    "ffmpeg-python":     "ffmpeg",
    "pillow":            "PIL",
    "pydantic":          "pydantic",
    "pydantic-settings": "pydantic_settings",
    "python-dotenv":     "dotenv",
    "aiofiles":          "aiofiles",
    "numpy":             "numpy",
}

for pkg_name, import_name in PACKAGES.items():
    check(
        f"Package: {pkg_name}",
        lambda m=import_name: __import__(m)
    )


# ── 5. Syntax check ───────────────────────────────────────────
print("\n[5] Checking file syntax...")

PYTHON_FILES = [
    "app/core/config.py",
    "app/utils/logger.py",
    "app/models/schemas.py",
]

def syntax_check(filepath):
    with open(filepath) as f:
        compile(f.read(), filepath, "exec")

for f in PYTHON_FILES:
    check(f"Syntax OK: {f}", lambda f=f: syntax_check(f))


# ── 6. Module imports ─────────────────────────────────────────
print("\n[6] Checking module imports...")

sys.path.insert(0, str(Path(".").resolve()))

def import_config():
    from app.core.config import settings
    assert settings.max_frames == 15
    assert settings.min_frames == 5
    print(f"       provider     : {settings.llm_provider}")
    print(f"       max_frames   : {settings.max_frames}")
    print(f"       scene_thresh : {settings.scene_threshold}")

def import_logger():
    from app.utils.logger import setup_logger
    logger = setup_logger("validation_test")
    assert logger is not None

def import_schemas():
    from app.models.schemas import (
        VideoAnalysisResponse,
        VideoInfo,
        AnalysisResult,
        HealthCheck,
    )
    from datetime import datetime
    # Make sure models instantiate correctly
    r = AnalysisResult(job_id="test-001", status="processing", created_at=datetime.now())
    assert r.status == "processing"
    assert r.description is None

check("Import: app.core.config",   import_config)
check("Import: app.utils.logger",  import_logger)
check("Import: app.models.schemas",import_schemas)


# ── 7. .env keys ──────────────────────────────────────────────
print("\n[7] Checking .env keys...")

def check_env_keys():
    with open(".env") as f:
        content = f.read()
    required = [
        "LLM_PROVIDER", "UPLOAD_DIR", "MAX_FRAMES",
        "MIN_FRAMES", "SCENE_THRESHOLD", "FRAME_QUALITY",
    ]
    missing = [k for k in required if k not in content]
    if missing:
        raise KeyError(f"Missing keys: {missing}")

check(".env has required keys", check_env_keys)


# ── Summary ───────────────────────────────────────────────────
print("\n" + "=" * 55)
passed = sum(1 for _, ok in results if ok)
failed = sum(1 for _, ok in results if not ok)
total  = len(results)

print(f"  Result: {passed}/{total} checks passed\n")

if failed == 0:
    print(f"  {PASS} All checks passed! You are ready for Step 2.")
else:
    print(f"  {FAIL} {failed} check(s) failed. Fix the issues above.\n")
    print("  Common fixes:")
    print("    Packages missing  →  pip install -r requirements.txt")
    print("    Files missing     →  re-create the missing files")
    print("    Folder missing    →  mkdir <folder_name>")

print("=" * 55 + "\n")
sys.exit(0 if failed == 0 else 1)