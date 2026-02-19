"""
STEP 4 VALIDATION (minimal)
Run: python step4_validate.py

Validates API routes and FastAPI app structure.
For full validation use: python step4_validation.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(".").resolve()))

PASS = "✅"
FAIL = "❌"


def main():
    print("\n" + "=" * 55)
    print("  STEP 4 VALIDATION: FastAPI Routes & App")
    print("=" * 55)

    # [1] Imports
    print("\n[1] Checking imports...")
    try:
        from app.api.routes import router, analyze_video, get_results
        print(f"  {PASS}  Import: app.api.routes")
    except Exception as e:
        print(f"  {FAIL}  Import: app.api.routes")
        print(f"       └─ {e}")
        sys.exit(1)
    try:
        from app.main import app
        assert app is not None
        print(f"  {PASS}  Import: app.main")
    except Exception as e:
        print(f"  {FAIL}  Import: app.main")
        print(f"       └─ {e}")
        sys.exit(1)

    # [2] App structure and routes
    print("\n[2] Checking FastAPI app structure...")
    try:
        from app.main import app
        assert app.title == "Video Analysis API"
        assert app.version == "1.0.0"
        assert "/docs" in str(app.docs_url)
        print(f"  {PASS}  App configured correctly")
    except Exception as e:
        print(f"  {FAIL}  App configured correctly")
        print(f"       └─ {e}")
        sys.exit(1)

    try:
        routes = [route.path for route in app.routes]
        required = [
            "/api/v1/analyze-video",
            "/api/v1/results/{job_id}",
            "/api/v1/health",
        ]
        for r in required:
            if r not in routes:
                raise AssertionError(f"Route not found: {r}")
        print(f"  {PASS}  Routes registered")
        print("\n       Registered routes:")
        for r in routes:
            if r.startswith("/api/v1"):
                print(f"       • {r}")
    except Exception as e:
        print(f"  {FAIL}  Routes registered")
        print(f"       └─ {e}")
        sys.exit(1)

    print("\n✅ Step 4 validation complete!")
    print("\nStep B: Start the server")
    print("Open a new terminal and run:")
    print("  cd video-analysis-api")
    print("  uvicorn app.main:app --reload --port 8000")
    print("\nYou should see:")
    print("  INFO:     Uvicorn running on http://127.0.0.1:8000")
    print("Leave this terminal running!")
    print("\nStep C: Test the API")
    print("In your original terminal, run:")
    print("  python step4_test_client.py uploads/test_video.mp4")
    print("=" * 55 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
