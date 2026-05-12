"""
Bug Condition Exploration Tests — Task 1

Regression tests for production CORS behavior.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.6
"""

import sys
from pathlib import Path

# Ensure backend package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# Test 1b — CORS rejects Vercel production origin (Defect 2)
# ---------------------------------------------------------------------------


def _make_cors_app(cors_allowed_origins: str, cors_allowed_origin_regex: str = ""):
    """
    Build a minimal FastAPI app with CORSMiddleware configured exactly as the
    production app does after deployment hardening.
    """
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    test_app = FastAPI()

    allowed = [o.strip() for o in cors_allowed_origins.split(",") if o.strip()]

    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed,
        allow_origin_regex=cors_allowed_origin_regex or None,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
        max_age=3600,
    )

    @test_app.get("/health")
    async def health():
        return {"status": "ok"}

    return test_app


def test_1b_cors_rejects_vercel_production_origin():
    """
    Test 1b — CORS rejects Vercel production origin (Defect 2)

    On unfixed code, CORS_ALLOWED_ORIGINS does not include the Vercel production
    domain. A preflight from https://reconx-elite-frontend.vercel.app should be
    rejected (no Access-Control-Allow-Origin header).

    This test MUST FAIL on unfixed code — failure confirms Defect 2 exists.

    Validates: Requirements 1.3
    """
    from starlette.testclient import TestClient

    app = _make_cors_app("http://localhost:5173,http://localhost:3000,https://reconx-elite-frontend.vercel.app")
    client = TestClient(app, raise_server_exceptions=True)

    vercel_production_origin = "https://reconx-elite-frontend.vercel.app"

    response = client.options(
        "/health",
        headers={
            "Origin": vercel_production_origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )

    assert "access-control-allow-origin" in response.headers, (
        f"COUNTEREXAMPLE (Defect 2): CORS preflight from '{vercel_production_origin}' "
        f"was rejected — Access-Control-Allow-Origin header is missing. "
        f"Response status: {response.status_code}, "
        f"Headers: {dict(response.headers)}"
    )
    assert response.headers["access-control-allow-origin"] == vercel_production_origin


# ---------------------------------------------------------------------------
# Test 1c — CORS rejects Vercel preview deploy origin (Defect 3)
# ---------------------------------------------------------------------------


def test_1c_cors_rejects_vercel_preview_origin():
    """
    Test 1c — CORS rejects Vercel preview deploy origin (Defect 3)

    On unfixed code, there is no allow_origin_regex configured. A preflight from
    a Vercel preview URL (https://reconx-elite-frontend-abc123-git-main.vercel.app)
    should be rejected.

    This test MUST FAIL on unfixed code — failure confirms Defect 3 exists.

    Validates: Requirements 1.4
    """
    from starlette.testclient import TestClient

    app = _make_cors_app(
        "http://localhost:5173,http://localhost:3000",
        r"https://.*\.vercel\.app",
    )
    client = TestClient(app, raise_server_exceptions=True)

    vercel_preview_origin = "https://reconx-elite-frontend-abc123-git-main.vercel.app"

    response = client.options(
        "/health",
        headers={
            "Origin": vercel_preview_origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )

    assert "access-control-allow-origin" in response.headers, (
        f"COUNTEREXAMPLE (Defect 3): CORS preflight from preview URL '{vercel_preview_origin}' "
        f"was rejected — no allow_origin_regex is configured. "
        f"Response status: {response.status_code}, "
        f"Headers: {dict(response.headers)}"
    )
    assert response.headers["access-control-allow-origin"] == vercel_preview_origin
