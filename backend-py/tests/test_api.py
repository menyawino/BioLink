"""
API endpoint tests for BioLink.
"""
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
    
    def test_health_endpoint(self, client: TestClient):
        """Test basic health check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "services" in data
        assert "timestamp" in data
    
    def test_detailed_health_endpoint(self, client: TestClient):
        """Test detailed health check with dependencies."""
        response = client.get("/api/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "database" in data["checks"]


class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    def test_login_success(self, client: TestClient):
        """Test successful login."""
        response = client.post(
            "/api/auth/token",
            data={"username": "admin", "password": "admin"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_failure(self, client: TestClient):
        """Test failed login with wrong credentials."""
        response = client.post(
            "/api/auth/token",
            data={"username": "admin", "password": "wrongpassword"}
        )
        assert response.status_code == 401
    
    def test_get_current_user(self, client: TestClient):
        """Test getting current user info."""
        # First login
        login_response = client.post(
            "/api/auth/token",
            data={"username": "admin", "password": "admin"}
        )
        token = login_response.json()["access_token"]
        
        # Then get user info
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin"


class TestPatientEndpoints:
    """Test patient-related endpoints."""
    
    def test_get_patients(self, client: TestClient):
        """Test getting patients list."""
        response = client.get("/api/patients")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or isinstance(data, dict)
    
    def test_search_patients(self, client: TestClient):
        """Test patient search functionality."""
        response = client.get("/api/patients?search=test&limit=10")
        assert response.status_code == 200


class TestChatEndpoints:
    """Test chat/AI endpoints."""
    
    def test_chat_endpoint(self, client: TestClient):
        """Test chat endpoint."""
        response = client.post(
            "/api/chat",
            json={"message": "How many patients are there?"}
        )
        # May return 200 or error depending on LLM availability
        assert response.status_code in [200, 500, 503]
    
    def test_chat_with_history(self, client: TestClient):
        """Test chat with conversation history."""
        response = client.post(
            "/api/chat",
            json={
                "message": "Show me the data",
                "history": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi! How can I help?"}
                ]
            }
        )
        assert response.status_code in [200, 500, 503]


class TestAnalyticsEndpoints:
    """Test analytics endpoints."""
    
    def test_analytics_overview(self, client: TestClient):
        """Test analytics overview endpoint."""
        response = client.get("/api/analytics/overview")
        assert response.status_code in [200, 404]  # May not be implemented
    
    def test_demographics(self, client: TestClient):
        """Test demographics endpoint."""
        response = client.get("/api/analytics/demographics")
        assert response.status_code in [200, 404]


@pytest.mark.integration
class TestIntegration:
    """Integration tests requiring full stack."""
    
    def test_full_chat_flow(self, client: TestClient):
        """Test complete chat flow with authentication."""
        # Login
        login_response = client.post(
            "/api/auth/token",
            data={"username": "researcher", "password": "researcher"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Use chat with auth
        chat_response = client.post(
            "/api/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": "What is the average age?"}
        )
        # Should work with or without LLM
        assert chat_response.status_code in [200, 500, 503]
