"""
Integration tests for Authentication API endpoints.
Tests the full auth flow: login, token refresh, logout.
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "backend"))

from server import app
from services.dao.json_dao import UserDAO
from services.security import PasswordService

password_service = PasswordService()


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def test_user():
    """Create a test user in the JSON storage."""
    user_dao = UserDAO()

    # Clean up any existing test user
    existing = user_dao.get_user_by_username("testuser")
    if existing:
        user_dao.delete_user(existing.id)

    # Create new test user
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "hashed_password": password_service.hash_password("testpass123"),
        "is_active": True,
        "is_verified": True
    }

    user = user_dao.create_user(user_data)
    yield user

    # Cleanup
    user_dao.delete_user(user.id)


class TestAuthenticationFlow:
    """Test complete authentication flow."""

    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post(
            "/auth/login",
            json={"username": "testuser", "password": "testpass123"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password."""
        response = client.post(
            "/auth/login",
            json={"username": "testuser", "password": "wrongpassword"}
        )

        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent username."""
        response = client.post(
            "/auth/login",
            json={"username": "nonexistent", "password": "anypassword"}
        )

        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]

    def test_access_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token."""
        response = client.get("/auth/me")

        assert response.status_code == 401

    def test_access_protected_endpoint_with_token(self, client, test_user):
        """Test accessing protected endpoint with valid token."""
        # Login first
        login_response = client.post(
            "/auth/login",
            json={"username": "testuser", "password": "testpass123"}
        )
        token = login_response.json()["access_token"]

        # Access protected endpoint
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    def test_refresh_token(self, client, test_user):
        """Test refreshing access token."""
        # Login first
        login_response = client.post(
            "/auth/login",
            json={"username": "testuser", "password": "testpass123"}
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh token
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_logout(self, client, test_user):
        """Test logout functionality."""
        # Login first
        login_response = client.post(
            "/auth/login",
            json={"username": "testuser", "password": "testpass123"}
        )
        token = login_response.json()["access_token"]

        # Logout
        response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert "Logged out successfully" in response.json()["message"]

        # Try using the token after logout (should fail)
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 401

    def test_invalid_token(self, client):
        """Test using an invalid token."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"}
        )

        assert response.status_code == 401

    def test_malformed_token(self, client):
        """Test using a malformed authorization header."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "InvalidFormat"}
        )

        assert response.status_code == 401


class TestUserRegistration:
    """Test user registration endpoints (if implemented)."""

    def test_registration_placeholder(self):
        """Placeholder for registration tests."""
        # TODO: Implement when registration endpoint is added
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
