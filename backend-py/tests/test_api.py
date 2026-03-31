"""
API endpoint tests for BioLink.
"""

import uuid
import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "name" in data
        assert "version" in data

    def test_request_id_generated(self, client: TestClient):
        """Test that X-Request-ID is generated for every response."""
        response = client.get("/")
        assert "x-request-id" in response.headers
        assert len(response.headers["x-request-id"]) > 0

    def test_request_id_echoed(self, client: TestClient):
        """Test that a provided X-Request-ID is echoed back."""
        response = client.get("/", headers={"X-Request-ID": "test-rid-123"})
        assert response.headers["x-request-id"] == "test-rid-123"

    def test_response_time_header(self, client: TestClient):
        """Test that X-Response-Time-Ms header is present."""
        response = client.get("/")
        assert "x-response-time-ms" in response.headers

    def test_health_endpoint(self, client: TestClient):
        """Test basic health check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "services" in data
        assert "database" in data["services"]
        assert "redis" in data["services"]
        assert "timestamp" in data

    def test_detailed_health_endpoint(self, client: TestClient):
        """Test detailed health check with dependencies."""
        response = client.get("/api/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "database" in data["checks"]
        assert "redis" in data["checks"]
        assert "pgvector" in data["checks"]


class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_login_success(self, client: TestClient):
        """Test successful login."""
        response = client.post(
            "/api/auth/token", data={"username": "admin", "password": "admin"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_failure(self, client: TestClient):
        """Test failed login with wrong credentials."""
        response = client.post(
            "/api/auth/token", data={"username": "admin", "password": "wrongpassword"}
        )
        assert response.status_code == 401

    def test_get_current_user(self, client: TestClient):
        """Test getting current user info."""
        # First login
        login_response = client.post(
            "/api/auth/token", data={"username": "admin", "password": "admin"}
        )
        token = login_response.json()["access_token"]

        # Then get user info
        response = client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin"

    def test_register_and_login_normalizes_username(self, client: TestClient):
        """Test registration/login work with mixed-case and surrounding whitespace."""
        suffix = uuid.uuid4().hex[:8]
        mixed_username = f"CaseUser_Test_{suffix}"
        normalized_username = f"caseuser_test_{suffix}"
        email = f"caseuser_test_{suffix}@example.org"

        register_response = client.post(
            "/api/auth/register",
            json={
                "username": f"  {mixed_username}  ",
                "email": f"  {email.upper()}  ",
                "password": "StrongPass123",
                "full_name": "Case User",
            },
        )
        assert register_response.status_code == 201
        created_user = register_response.json()
        assert created_user["username"] == normalized_username
        assert created_user["email"] == email

        login_response = client.post(
            "/api/auth/token",
            data={"username": f"  {normalized_username.upper()}  ", "password": "StrongPass123"},
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data

    def test_admin_can_manage_other_users(self, client: TestClient):
        """Admin can create, list, update authorities, revoke, and delete users."""
        login_response = client.post(
            "/api/auth/token", data={"username": "admin", "password": "admin"}
        )
        assert login_response.status_code == 200
        admin_token = login_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        create_response = client.post(
            "/api/auth/users",
            headers=admin_headers,
            json={
                "username": "admin_manage_test_user",
                "email": "admin_manage_test_user@example.org",
                "password": "StrongPass123",
                "full_name": "Managed User",
                "role": "viewer",
                "scopes": ["read"],
            },
        )
        assert create_response.status_code == 201
        created = create_response.json()
        assert created["username"] == "admin_manage_test_user"
        assert created["role"] == "viewer"

        list_response = client.get("/api/auth/users", headers=admin_headers)
        assert list_response.status_code == 200
        users = list_response.json()
        assert any(u["username"] == "admin_manage_test_user" for u in users)

        update_response = client.put(
            "/api/auth/users/admin_manage_test_user",
            headers=admin_headers,
            json={
                "role": "researcher",
                "scopes": ["read", "write"],
                "disabled": True,
            },
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["role"] == "researcher"
        assert updated["disabled"] is True
        assert sorted(updated["scopes"]) == ["read", "write"]

        delete_response = client.delete(
            "/api/auth/users/admin_manage_test_user", headers=admin_headers
        )
        assert delete_response.status_code == 200


class TestPatientEndpoints:
    """Test patient-related endpoints."""

    def test_get_patients(self, client: TestClient, auth_headers: dict):
        """Test getting patients list."""
        response = client.get("/api/patients", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or isinstance(data, dict)

    def test_search_patients(self, client: TestClient, auth_headers: dict):
        """Test patient search functionality."""
        response = client.get("/api/patients?search=test&limit=10", headers=auth_headers)
        assert response.status_code == 200


class TestChatEndpoints:
    """Test chat/AI endpoints."""

    def test_chat_endpoint(self, client: TestClient, auth_headers: dict):
        """Test chat endpoint."""
        response = client.post(
            "/api/chat",
            headers=auth_headers,
            json={"message": "How many patients are there?"},
        )
        # May return 200 or error depending on LLM availability
        assert response.status_code in [200, 500, 503]

    def test_chat_with_history(self, client: TestClient, auth_headers: dict):
        """Test chat with conversation history."""
        response = client.post(
            "/api/chat",
            headers=auth_headers,
            json={
                "message": "Show me the data",
                "history": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi! How can I help?"},
                ],
            },
        )
        assert response.status_code in [200, 500, 503]


class TestAnalyticsEndpoints:
    """Test analytics endpoints."""

    def test_analytics_overview(self, client: TestClient, auth_headers: dict):
        """Test analytics overview endpoint."""
        response = client.get("/api/analytics/overview", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "hasAgeData" in data["data"]
        assert "ageDataCount" in data["data"]

    def test_demographics(self, client: TestClient, auth_headers: dict):
        """Test demographics endpoint."""
        response = client.get("/api/analytics/demographics", headers=auth_headers)
        assert response.status_code == 200

    def test_cohort_filters(self, client: TestClient, auth_headers: dict):
        """Test live cohort filter metadata endpoint."""
        response = client.get("/api/analytics/cohort-filters", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "genders" in data["data"]
        assert "nationalities" in data["data"]
        assert "regions" in data["data"]
        assert "diagnoses" in data["data"]
        assert "riskFactors" in data["data"]
        assert "dataTypes" in data["data"]


class TestHarmonizationEndpoints:
    """Test harmonization endpoints."""

    def test_harmonization_tiers(self, client: TestClient, auth_headers: dict):
        """Test harmonization tiers endpoint."""
        response = client.get("/api/harmonization/tiers", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0

    def test_provenance_summary(self, client: TestClient, auth_headers: dict):
        """Test provenance summary endpoint."""
        response = client.get(
            "/api/harmonization/provenance/summary", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_records"] > 0

    def test_provenance_records(self, client: TestClient, auth_headers: dict):
        """Test provenance records endpoint with filters."""
        response = client.get(
            "/api/harmonization/provenance?limit=10", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert len(data["data"]) > 0

    def test_comparability_report(self, client: TestClient, auth_headers: dict):
        """Test comparability report endpoint."""
        response = client.get("/api/harmonization/comparability", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]

    def test_dictionary(self, client: TestClient, auth_headers: dict):
        """Test harmonization data dictionary endpoint."""
        response = client.get("/api/harmonization/dictionary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)


@pytest.mark.integration
class TestIntegration:
    """Integration tests requiring full stack."""

    def test_full_chat_flow(self, client: TestClient):
        """Test complete chat flow with authentication."""
        # Login
        login_response = client.post(
            "/api/auth/token", data={"username": "researcher", "password": "researcher"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Use chat with auth
        chat_response = client.post(
            "/api/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": "What is the average age?"},
        )
        # Should work with or without LLM
        assert chat_response.status_code in [200, 500, 503]
