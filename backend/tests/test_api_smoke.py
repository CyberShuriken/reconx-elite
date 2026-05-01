"""HTTP-level smoke tests for the FastAPI app (middleware + dependency overrides)."""

import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token
from app.main import app
from app.models.user import User
from fastapi.testclient import TestClient


class TestAPISmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._orig_secret = settings.jwt_secret_key
        settings.jwt_secret_key = "test-api-smoke-secret-key-for-ci"

    @classmethod
    def tearDownClass(cls):
        settings.jwt_secret_key = cls._orig_secret

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_health_root(self):
        client = TestClient(app)
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "ok")

    def test_protected_route_missing_token(self):
        client = TestClient(app)
        response = client.get("/targets")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json().get("detail"), "Missing bearer token")

    def test_protected_route_invalid_token(self):
        client = TestClient(app)
        response = client.get(
            "/targets",
            headers={"Authorization": "Bearer not-a-valid-jwt"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json().get("detail"), "Invalid access token")

    def test_list_targets_with_dependency_overrides(self):
        fake_user = User()
        fake_user.id = 1
        fake_user.email = "smoke@test.local"
        fake_user.role = "user"

        db = MagicMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=result)

        def override_get_current_user():
            return fake_user

        async def override_get_db():
            yield db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        token = create_access_token("1", "user")
        client = TestClient(app)
        response = client.get("/targets", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])


if __name__ == "__main__":
    unittest.main()
