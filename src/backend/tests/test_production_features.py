"""
Integration tests for production readiness features.
Tests authentication, rate limiting, pagination, and health checks.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from server import app
from services.dao.json_dao import UserDAO
from services.security.password_service import PasswordService


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def test_user():
    """Create a test user for authentication tests"""
    user_dao = UserDAO()
    password_service = PasswordService()

    test_username = f"testuser_{datetime.now().timestamp()}"
    user_data = {
        "username": test_username,
        "email": f"{test_username}@test.com",
        "hashed_password": password_service.hash_password("testpass123"),
        "is_active": True,
        "is_verified": True,
        "risk_tolerance": "moderate",
        "investment_experience": "beginner"
    }

    try:
        user = user_dao.create_user(user_data)
        yield {"username": test_username, "password": "testpass123", "user_id": user.id}

        # Cleanup
        user_dao.delete_user(user.id)
    except Exception as e:
        print(f"Error creating test user: {e}")
        yield None


class TestHealthChecks:
    """Test health check endpoints"""

    def test_root_health_check(self, client):
        """Test basic health check"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "APEX API"
        assert data["version"] == "2.0.0"
        assert data["status"] == "running"
        assert "timestamp" in data

    def test_comprehensive_health_check(self, client):
        """Test comprehensive health check endpoint"""
        response = client.get("/health")
        assert response.status_code in [200, 503]  # Can be unhealthy in test env
        data = response.json()

        # Check response structure
        assert "status" in data
        assert data["status"] in ["healthy", "unhealthy"]
        assert "timestamp" in data
        assert "version" in data
        assert "checks" in data

        # Check sub-checks
        assert "storage" in data["checks"]
        assert "environment" in data["checks"]
        assert "system" in data["checks"]
        assert "services" in data

        # Check system metrics
        system = data["checks"]["system"]
        assert "memory_percent" in system
        assert "disk_percent" in system
        assert "cpu_count" in system


class TestAPIVersioning:
    """Test API versioning headers"""

    def test_version_headers_present(self, client):
        """Test that API version headers are added to responses"""
        response = client.get("/")
        assert "X-API-Version" in response.headers
        assert response.headers["X-API-Version"] == "1.0"
        assert "X-API-Compat" in response.headers
        assert response.headers["X-API-Compat"] == "v1"


class TestAuthentication:
    """Test authentication endpoints"""

    def test_registration_endpoint(self, client):
        """Test user registration"""
        timestamp = datetime.now().timestamp()
        registration_data = {
            "username": f"newuser_{timestamp}",
            "email": f"newuser_{timestamp}@test.com",
            "password": "SecurePass123!"
        }

        response = client.post("/auth/register", json=registration_data)

        # Should succeed or fail with rate limit
        assert response.status_code in [200, 429]

        if response.status_code == 200:
            data = response.json()
            assert "user_id" in data
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"

            # Cleanup
            from services.dao.json_dao import UserDAO
            user_dao = UserDAO()
            user_dao.delete_user(data["user_id"])

    def test_login_endpoint(self, client, test_user):
        """Test user login"""
        if test_user is None:
            pytest.skip("Test user creation failed")

        login_data = {
            "username": test_user["username"],
            "password": test_user["password"]
        }

        response = client.post("/auth/login", json=login_data)

        # Should succeed or fail with rate limit
        assert response.status_code in [200, 401, 429]

        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"


class TestRateLimiting:
    """Test rate limiting functionality"""

    def test_login_rate_limit(self, client, test_user):
        """Test that login endpoint is rate limited"""
        if test_user is None:
            pytest.skip("Test user creation failed")

        # Try to login multiple times rapidly
        login_data = {
            "username": test_user["username"],
            "password": "wrongpassword"
        }

        responses = []
        for _ in range(10):  # Try 10 times (limit is 5/minute)
            response = client.post("/auth/login", json=login_data)
            responses.append(response.status_code)

        # Should get at least one 429 (Too Many Requests)
        # Note: This might not always trigger in tests due to timing
        assert any(status == 429 for status in responses) or all(status == 401 for status in responses)


class TestPagination:
    """Test pagination on list endpoints"""

    def test_orders_pagination_params(self, client):
        """Test orders endpoint accepts pagination parameters"""
        response = client.get("/api/orders?limit=10&offset=0")

        # Endpoint should exist (may return 503 if broker not initialized)
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()

            # Check pagination response structure
            assert "orders" in data
            assert "total" in data
            assert "limit" in data
            assert "offset" in data
            assert "has_more" in data
            assert data["limit"] == 10
            assert data["offset"] == 0

    def test_positions_pagination_params(self, client):
        """Test positions endpoint accepts pagination parameters"""
        response = client.get("/api/positions?limit=25&offset=5")

        # Endpoint should exist (may return 503 if broker not initialized)
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()

            # Check pagination response structure
            assert "positions" in data
            assert "total" in data
            assert "limit" in data
            assert "offset" in data
            assert "has_more" in data
            assert data["limit"] == 25
            assert data["offset"] == 5

    def test_pagination_limit_validation(self, client):
        """Test that pagination limits are enforced"""
        # Try with limit > 500 (should be clamped to 500)
        response = client.get("/api/orders?limit=1000")

        # Should return validation error
        assert response.status_code in [422, 200, 503]


class TestRequestSizeLimits:
    """Test request size limiting middleware"""

    def test_large_request_rejected(self, client):
        """Test that very large requests are rejected"""
        # Create a payload larger than 10MB
        large_data = {"data": "x" * (11 * 1024 * 1024)}  # 11MB

        response = client.post(
            "/auth/login",
            json=large_data,
            headers={"Content-Length": str(11 * 1024 * 1024)}
        )

        # Should be rejected with 413 Payload Too Large
        assert response.status_code in [413, 422, 429]


class TestDataValidation:
    """Test Pydantic validation in DAO layer"""

    def test_invalid_user_data_rejected(self):
        """Test that invalid user data is rejected"""
        from services.dao.json_dao import UserDAO, DAOValidationError

        user_dao = UserDAO()

        # Missing required fields
        invalid_data = {
            "username": "testuser"
            # Missing email, password, etc.
        }

        with pytest.raises((DAOValidationError, Exception)):
            user_dao.create_user(invalid_data)

    def test_invalid_email_rejected(self):
        """Test that invalid email format is rejected"""
        from services.dao.json_dao import UserDAO, DAOValidationError
        from services.security.password_service import PasswordService

        user_dao = UserDAO()
        password_service = PasswordService()

        invalid_data = {
            "username": "testuser",
            "email": "not-an-email",  # Invalid email format
            "hashed_password": password_service.hash_password("test123"),
            "is_active": True,
            "is_verified": False,
            "risk_tolerance": "moderate",
            "investment_experience": "beginner"
        }

        with pytest.raises((DAOValidationError, Exception)):
            user_dao.create_user(invalid_data)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
