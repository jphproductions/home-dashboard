"""Unit tests for main.py error handlers and lifecycle."""

from fastapi.testclient import TestClient
from slowapi.errors import RateLimitExceeded

from home_dashboard.exceptions import DashboardException, ErrorCode
from home_dashboard.main import app


class TestExceptionHandlers:
    """Tests for exception handlers in main.py."""

    def test_dashboard_exception_handler_exists(self):
        """Test that DashboardException handler is registered."""
        assert DashboardException in app.exception_handlers

    def test_rate_limit_exceeded_handler(self):
        """Test that rate limit exceeded handler is registered."""
        assert RateLimitExceeded in app.exception_handlers


class TestLifecycle:
    """Tests for app lifecycle events."""

    def test_app_has_routers(self):
        """Test that app has routers registered."""
        assert hasattr(app, "router")
        assert len(app.routes) > 0

    def test_app_state_has_limiter(self):
        """Test that app has rate limiter configured."""
        from home_dashboard.main import limiter

        assert limiter is not None
        assert limiter.enabled


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_endpoint_returns_html(self):
        """Test root endpoint returns HTML dashboard."""
        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert b"<!DOCTYPE html>" in response.content

    def test_health_endpoint(self):
        """Test health check endpoint returns status."""
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestExceptionCreation:
    """Tests for creating dashboard exceptions."""

    def test_create_dashboard_exception(self):
        """Test creating a DashboardException."""
        exc = DashboardException(
            message="Test error", code=ErrorCode.DASHBOARD_ERROR, status_code=500, details={"key": "value"}
        )

        assert exc.message == "Test error"
        assert exc.code == ErrorCode.DASHBOARD_ERROR
        assert exc.status_code == 500
        assert exc.details == {"key": "value"}

    def test_dashboard_exception_defaults(self):
        """Test DashboardException with defaults."""
        exc = DashboardException(message="Simple error")

        assert exc.message == "Simple error"
        assert exc.code == ErrorCode.DASHBOARD_ERROR
        assert exc.status_code == 500
        assert exc.details == {}
