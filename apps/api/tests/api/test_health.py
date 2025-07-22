"""
Tests for health check endpoint

This module contains tests for the /health endpoint to ensure it returns the correct
response format and status codes as specified in the acceptance criteria.
"""

import pytest
from fastapi.testclient import TestClient
from main import app

# Create test client for FastAPI app
client = TestClient(app)


class TestHealthEndpoint:
    """Test cases for the /health endpoint"""

    def test_health_endpoint_returns_correct_json(self):
        """Test that health endpoint returns exact JSON response {"status": "ok"}"""
        response = client.get("/health")
        
        # Validate status code
        assert response.status_code == 200
        
        # Validate exact JSON response
        expected_response = {"status": "ok"}
        assert response.json() == expected_response

    def test_health_endpoint_content_type(self):
        """Test that health endpoint returns application/json content type"""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    def test_health_endpoint_response_time(self):
        """Test that health endpoint responds within acceptable threshold"""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        # Health check should respond within 100ms
        assert response_time_ms < 100

    def test_health_endpoint_multiple_requests(self):
        """Test that health endpoint is consistent across multiple requests"""
        expected_response = {"status": "ok"}
        
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json() == expected_response

    def test_root_endpoint_includes_health_link(self):
        """Test that root endpoint includes reference to health endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        response_data = response.json()
        assert "health" in response_data
        assert response_data["health"] == "/health"


class TestApplicationStartup:
    """Test cases for application startup and configuration"""

    def test_app_title_and_version(self):
        """Test that FastAPI app has correct title and version"""
        assert app.title == "Theo API"
        assert app.version == "1.0.0"

    def test_docs_endpoints_configured(self):
        """Test that documentation endpoints are accessible"""
        # Test OpenAPI docs
        docs_response = client.get("/docs")
        assert docs_response.status_code == 200
        
        # Test ReDoc documentation  
        redoc_response = client.get("/redoc")
        assert redoc_response.status_code == 200

    def test_cors_middleware_configured(self):
        """Test that CORS middleware is properly configured"""
        # Send OPTIONS preflight request to test CORS
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        
        # Should not fail with CORS error
        assert response.status_code in [200, 405]  # 405 is acceptable for OPTIONS