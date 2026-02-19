"""
STEP 5 VALIDATION SCRIPT
Location: video-analysis-api/step5_validate.py

Validates LLM service integration.

Usage:
    python step5_validate.py
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
print("  STEP 5 VALIDATION: LLM Integration")
print("=" * 55)


# ── 1. Import checks ──────────────────────────────────────────
print("\n[1] Checking imports...")


def import_llm_service():
    from app.services.llm_service import LLMService


def import_updated_routes():
    from app.api.routes import llm_service
    assert llm_service is not None


check("Import: app.services.llm_service", import_llm_service)
check("Import: llm_service in routes", import_updated_routes)


# ── 2. API Key Configuration ──────────────────────────────────
print("\n[2] Checking API key configuration...")


def check_api_key():
    from app.core.config import settings
    
    if not settings.google_api_key:
        raise ValueError("GOOGLE_API_KEY not set in .env")
    
    if settings.google_api_key == "your_google_api_key_here":
        raise ValueError("Please set your actual Google API key in .env")
    
    if not settings.google_api_key.startswith("AIza"):
        raise ValueError("Google API keys should start with 'AIza'")
    
    print(f"\n       Provider: {settings.llm_provider}")
    print(f"       API Key : {settings.google_api_key[:10]}...")


def check_provider():
    from app.core.config import settings
    assert settings.llm_provider == "google"


check("Google API key configured", check_api_key)
check("Provider set to 'google'", check_provider)


# ── 3. LLM Service Initialization ─────────────────────────────
print("\n[3] Initializing LLM service...")


llm = None


def create_llm_service():
    global llm
    from app.services.llm_service import LLMService
    
    llm = LLMService()
    assert llm is not None
    assert llm.model is not None
    
    print(f"\n       Model initialized: gemini-2.5-flash")


check("LLM service created", create_llm_service)


# ── 4. Test with sample frames ────────────────────────────────
print("\n[4] Testing frame analysis (optional - requires frames)...")

# This test is optional since it requires actual frame files
# and makes a real API call to Google
test_frames_path = Path("temp")

if test_frames_path.exists() and any(test_frames_path.glob("*.jpg")):
    def test_analysis():
        frame_files = sorted(list(test_frames_path.glob("*.jpg")))[:3]
        
        if not frame_files:
            raise Exception("No frame files found in temp/")
        
        frame_paths = [str(f) for f in frame_files]
        
        print(f"\n       Testing with {len(frame_paths)} frames...")
        description = llm.analyze_frames(frame_paths)
        
        assert len(description) > 50, "Description too short"
        
        print(f"       Description length: {len(description)} chars")
        print(f"       Preview: {description[:100]}...")
    
    check("Frame analysis works", test_analysis)
else:
    print(f"  ⏭️   Skipping (no test frames available)")
    print(f"       This will be tested in the full API test")


# ── 5. Routes updated ─────────────────────────────────────────
print("\n[5] Checking routes are updated...")


def check_routes_have_llm():
    from app.api.routes import process_video, llm_service
    
    import inspect
    source = inspect.getsource(process_video)
    
    # Check that process_video calls llm_service
    assert "llm_service.analyze_frames" in source, \
        "process_video() doesn't call llm_service.analyze_frames()"


check("Routes use LLM service", check_routes_have_llm)


# ── Summary ───────────────────────────────────────────────────
print("\n" + "=" * 55)
passed = sum(1 for _, ok in results if ok)
failed = sum(1 for _, ok in results if not ok)

print(f"  Result: {passed}/{len(results)} checks passed\n")

if failed == 0:
    print(f"  {PASS} Step 5 validation complete!")
    print(f"\n  Next steps:")
    print(f"    1. Restart your server (Ctrl+C then restart)")
    print(f"    2. Run: python step5_test_client.py uploads/test_video.mp4")
    print(f"    3. Your video will get a real AI description!")
else:
    print(f"  {FAIL} {failed} check(s) failed.")
    print(f"\n  Common fixes:")
    print(f"    • API key not set     → Add GOOGLE_API_KEY to .env")
    print(f"    • Wrong provider      → Set LLM_PROVIDER=google in .env")
    print(f"    • Import errors       → pip install google-generativeai")

print("=" * 55 + "\n")
sys.exit(0 if failed == 0 else 1)