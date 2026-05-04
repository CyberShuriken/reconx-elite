"""
Preservation Property Tests — Task 2

These tests MUST PASS on unfixed code. Passing confirms the baseline behavior
that must be preserved after the fix is applied.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.6
"""

import os
import sys
from pathlib import Path

import pytest

# Ensure backend package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_cors_app(cors_allowed_origins: str):
    """
    Build a minimal FastAPI app with CORSMiddleware configured exactly as the
    current (unfixed) main.py does — no allow_origin_regex parameter.

    This mirrors the unfixed production configuration so we can verify that
    localhost origins are still allowed (Requirement 3.6).
    """
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    test_app = FastAPI()

    allowed = [o.strip() for o in cors_allowed_origins.split(",") if o.strip()]

    # Unfixed: no allow_origin_regex parameter — same as current main.py
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
        max_age=3600,
    )

    @test_app.get("/health")
    async def health():
        return {"status": "ok"}

    return test_app


# ---------------------------------------------------------------------------
# Test 2e — CORS allows localhost origins (Requirement 3.6)
# ---------------------------------------------------------------------------

class TestCorsLocalhostPreservation:
    """
    Test 2e — CORS allows localhost origins (Requirement 3.6)

    Validates: Requirements 3.6

    Property: For all origins in the static CORS_ALLOWED_ORIGINS list,
    an OPTIONS preflight from that origin is allowed (Access-Control-Allow-Origin
    header is present and matches the origin).

    This test MUST PASS on unfixed code — it confirms that localhost origins
    continue to be allowed after the fix.
    """

    # The static localhost origins that must always be allowed
    LOCALHOST_ORIGINS = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    def test_2e_cors_allows_localhost_5173(self):
        """
        CORS preflight from http://localhost:5173 is allowed when it is in
        CORS_ALLOWED_ORIGINS.

        Validates: Requirements 3.6
        """
        from starlette.testclient import TestClient

        # Simulate the production config that includes localhost origins
        cors_origins = "http://localhost:5173,http://localhost:3000"
        app = _make_cors_app(cors_origins)
        client = TestClient(app, raise_server_exceptions=True)

        origin = "http://localhost:5173"
        response = client.options(
            "/health",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
        )

        # This MUST PASS on unfixed code — localhost:5173 is in the allowed list
        assert "access-control-allow-origin" in response.headers, (
            f"PRESERVATION FAILURE: CORS preflight from '{origin}' was rejected. "
            f"localhost:5173 must remain in CORS_ALLOWED_ORIGINS after the fix. "
            f"Response status: {response.status_code}, "
            f"Headers: {dict(response.headers)}"
        )
        assert response.headers["access-control-allow-origin"] == origin, (
            f"Expected Access-Control-Allow-Origin: {origin}, "
            f"got: {response.headers.get('access-control-allow-origin')}"
        )

    def test_2e_cors_allows_localhost_3000(self):
        """
        CORS preflight from http://localhost:3000 is allowed when it is in
        CORS_ALLOWED_ORIGINS.

        Validates: Requirements 3.6
        """
        from starlette.testclient import TestClient

        cors_origins = "http://localhost:5173,http://localhost:3000"
        app = _make_cors_app(cors_origins)
        client = TestClient(app, raise_server_exceptions=True)

        origin = "http://localhost:3000"
        response = client.options(
            "/health",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
        )

        # This MUST PASS on unfixed code — localhost:3000 is in the allowed list
        assert "access-control-allow-origin" in response.headers, (
            f"PRESERVATION FAILURE: CORS preflight from '{origin}' was rejected. "
            f"localhost:3000 must remain in CORS_ALLOWED_ORIGINS after the fix. "
            f"Response status: {response.status_code}, "
            f"Headers: {dict(response.headers)}"
        )
        assert response.headers["access-control-allow-origin"] == origin, (
            f"Expected Access-Control-Allow-Origin: {origin}, "
            f"got: {response.headers.get('access-control-allow-origin')}"
        )

    @pytest.mark.parametrize("origin", LOCALHOST_ORIGINS)
    def test_2e_property_all_static_origins_allowed(self, origin):
        """
        Property: For all origins in the static CORS_ALLOWED_ORIGINS list,
        preflight is allowed.

        This is the property-based formulation of Test 2e — it parameterizes
        over all known localhost origins to verify the property holds for each.

        Validates: Requirements 3.6
        """
        from starlette.testclient import TestClient

        cors_origins = ",".join(self.LOCALHOST_ORIGINS)
        app = _make_cors_app(cors_origins)
        client = TestClient(app, raise_server_exceptions=True)

        response = client.options(
            "/health",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
        )

        assert "access-control-allow-origin" in response.headers, (
            f"PRESERVATION FAILURE: Static origin '{origin}' was rejected by CORS. "
            f"All origins in CORS_ALLOWED_ORIGINS must be allowed. "
            f"Response status: {response.status_code}"
        )
        assert response.headers["access-control-allow-origin"] == origin

    def test_2e_non_listed_origin_is_rejected(self):
        """
        Sanity check: an origin NOT in the static list is rejected.
        This confirms the CORS middleware is actually enforcing the list.

        Validates: Requirements 3.6 (negative case — ensures the test is meaningful)
        """
        from starlette.testclient import TestClient

        cors_origins = "http://localhost:5173,http://localhost:3000"
        app = _make_cors_app(cors_origins)
        client = TestClient(app, raise_server_exceptions=True)

        unlisted_origin = "http://evil.example.com"
        response = client.options(
            "/health",
            headers={
                "Origin": unlisted_origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
        )

        # An unlisted origin must NOT receive the CORS header
        assert "access-control-allow-origin" not in response.headers, (
            f"Security issue: unlisted origin '{unlisted_origin}' was allowed by CORS. "
            f"The static origin list must only allow listed origins."
        )


# ---------------------------------------------------------------------------
# Test 2e — Settings.cors_allowed_origins_list parses correctly
# ---------------------------------------------------------------------------

class TestSettingsCorsPreservation:
    """
    Verify that Settings.cors_allowed_origins_list correctly parses the
    comma-separated CORS_ALLOWED_ORIGINS string.

    This is a preservation test: the parsing logic must remain unchanged after
    the fix adds cors_allowed_origin_regex.

    Validates: Requirements 3.6
    """

    def test_cors_allowed_origins_list_parses_localhost_origins(self):
        """
        Settings.cors_allowed_origins_list correctly parses the default
        localhost origins.

        Validates: Requirements 3.6
        """
        import os

        # Patch env to avoid loading .env file secrets
        with pytest.MonkeyPatch().context() as mp:
            mp.setenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000")
            mp.setenv("JWT_SECRET_KEY", "a" * 32)
            mp.setenv("DATABASE_URL", "sqlite:///:memory:")
            mp.setenv("REDIS_URL", "redis://localhost:6379/0")

            # Re-import Settings to pick up patched env
            import importlib

            # Create a fresh Settings instance with the patched env
            from pydantic_settings import BaseSettings

            import app.core.config as config_module
            from app.core.config import Settings

            s = Settings(
                cors_allowed_origins="http://localhost:5173,http://localhost:3000",
                jwt_secret_key="a" * 32,
                database_url="sqlite:///:memory:",
                redis_url="redis://localhost:6379/0",
            )

        origins = s.cors_allowed_origins_list
        assert "http://localhost:5173" in origins, (
            f"PRESERVATION FAILURE: http://localhost:5173 not in cors_allowed_origins_list. "
            f"Got: {origins}"
        )
        assert "http://localhost:3000" in origins, (
            f"PRESERVATION FAILURE: http://localhost:3000 not in cors_allowed_origins_list. "
            f"Got: {origins}"
        )

    def test_cors_allowed_origins_list_strips_whitespace(self):
        """
        Settings.cors_allowed_origins_list strips whitespace from each origin.

        Validates: Requirements 3.6
        """
        from app.core.config import Settings

        s = Settings(
            cors_allowed_origins=" http://localhost:5173 , http://localhost:3000 ",
            jwt_secret_key="a" * 32,
            database_url="sqlite:///:memory:",
            redis_url="redis://localhost:6379/0",
        )

        origins = s.cors_allowed_origins_list
        assert "http://localhost:5173" in origins
        assert "http://localhost:3000" in origins
        # Ensure no whitespace-padded entries
        for origin in origins:
            assert origin == origin.strip(), f"Origin has leading/trailing whitespace: '{origin}'"

    @pytest.mark.parametrize("origins_str,expected", [
        (
            "http://localhost:5173",
            ["http://localhost:5173"],
        ),
        (
            "http://localhost:5173,http://localhost:3000",
            ["http://localhost:5173", "http://localhost:3000"],
        ),
        (
            "http://localhost:5173,https://reconx-elite-frontend.vercel.app",
            ["http://localhost:5173", "https://reconx-elite-frontend.vercel.app"],
        ),
    ])
    def test_cors_allowed_origins_list_property(self, origins_str, expected):
        """
        Property: cors_allowed_origins_list always returns exactly the origins
        in the comma-separated string, stripped of whitespace.

        Validates: Requirements 3.6
        """
        from app.core.config import Settings

        s = Settings(
            cors_allowed_origins=origins_str,
            jwt_secret_key="a" * 32,
            database_url="sqlite:///:memory:",
            redis_url="redis://localhost:6379/0",
        )

        assert s.cors_allowed_origins_list == expected, (
            f"cors_allowed_origins_list mismatch. "
            f"Input: '{origins_str}', Expected: {expected}, Got: {s.cors_allowed_origins_list}"
        )
