"""
STEP 4 VALIDATION SCRIPT
Location: video-analysis-api/step4_validate.py

This validates that the API routes and FastAPI app are set up correctly.
It does NOT start the server - use step4_test_client.py for that.

Usage:
    python step4_validate.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(".").resolve()))

PASS = "✅"
FAIL = "❌"
results = []


def check(label, fn):
    try:
        fn()
        print(f"  {PASS}  {label}")
        results.append((label, True))
    except Exception as e:
        print(f"  {FAIL}  {label}")
        print(f"       └─ {e}")
        results.append((label, False))


print("\n" + "=" * 55)
print("  STEP 4 VALIDATION: FastAPI Routes & App")
print("=" * 55)


# ── 1. Import checks ──────────────────────────────────────────
print("\n[1] Checking imports...")


def import_routes():
    from app.api.routes import router, analyze_video, get_results


def import_main():
    from app.main import app
    assert app is not None


check("Import: app.api.routes", import_routes)
check("Import: app.main", import_main)


# ── 2. FastAPI app structure ──────────────────────────────────
print("\n[2] Checking FastAPI app structure...")


def check_app_config():
    from app.main import app

    assert app.title == "Video Analysis API"
    assert app.version == "1.0.0"
    assert "/docs" in str(app.docs_url)


def check_routes_registered():
    from app.main import app

    routes = [route.path for route in app.routes]

    required_routes = [
        "/api/v1/analyze-video",
        "/api/v1/results/{job_id}",
        "/api/v1/health",
    ]

    for r in required_routes:
        assert r in routes, f"Route not found: {r}"

    print(f"\n       Registered routes:")
    for r in routes:
        if r.startswith("/api/v1"):
            print(f"       • {r}")


check("App configured correctly", check_app_config)
check("Routes registered", check_routes_registered)


# ── 3. Endpoint definitions ───────────────────────────────────
print("\n[3] Checking endpoint definitions...")


def check_endpoints():
    from app.api.routes import router

    endpoint_names = [route.name for route in router.routes]

    required = ["analyze_video", "get_results", "health_check"]
    for name in required:
        assert name in endpoint_names, f"Endpoint missing: {name}"

    print(f"\n       Endpoints defined:")
    for name in endpoint_names:
        print(f"       • {name}")


check("All endpoints defined", check_endpoints)


# ── 4. Job storage initialized ────────────────────────────────
print("\n[4] Checking job storage...")


def check_job_storage():
    from app.api.routes import analysis_jobs

    assert isinstance(analysis_jobs, dict)
    assert len(analysis_jobs) == 0  # starts empty


check("Job storage initialized", check_job_storage)


# ── 5. Video processor in routes ──────────────────────────────
print("\n[5] Checking services are initialized...")


def check_services():
    from app.api.routes import video_processor

    assert video_processor is not None
    assert hasattr(video_processor, "extract_frames_smart")


check("VideoProcessor initialized", check_services)


# ── 6. Response models ────────────────────────────────────────
print("\n[6] Checking response models...")


def check_models():
    from app.models.schemas import (
        VideoAnalysisResponse,
        AnalysisResult,
        HealthCheck,
    )

    # Test instantiation
    from datetime import datetime

    resp = VideoAnalysisResponse(
        job_id="test", status="processing", message="test"
    )
    assert resp.job_id == "test"

    result = AnalysisResult(
        job_id="test", status="processing", created_at=datetime.now()
    )
    assert result.status == "processing"

    health = HealthCheck(status="healthy", version="1.0.0", provider="local")
    assert health.status == "healthy"


check("Response models work", check_models)


# ── Summary ───────────────────────────────────────────────────
print("\n" + "=" * 55)
passed = sum(1 for _, ok in results if ok)
failed = sum(1 for _, ok in results if not ok)

print(f"  Result: {passed}/{len(results)} checks passed\n")

if failed == 0:
    print(f"  {PASS} Step 4 validation complete!")
    print(f"\n  Next: Start the server and test it:")
    print(f"    uvicorn app.main:app --reload --port 8000")
    print(f"\n  Then run: python step4_test_client.py")
else:
    print(f"  {FAIL} {failed} check(s) failed.")

print("=" * 55 + "\n")
sys.exit(0 if failed == 0 else 1)