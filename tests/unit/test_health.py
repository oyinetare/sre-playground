from unittest.mock import patch


class TestHealthEndpoints:
    """Test health check endpoints - critical for SRE"""

    def test_liveness_probe_always_returns_200(self, client):
        """Liveness should return 200 even if dependencies are down"""
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json() == {"status": "alive"}

    def test_readiness_with_healthy_dependencies(self, client):
        """Readiness should return 200 when all dependencies are healthy"""
        response = client.get("/health/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"

    @patch("app.db.database.SessionLocal")
    def test_readiness_with_database_down(self, mock_session, client):
        """Readiness should return 503 when database is down"""
        # Mock database connection failure
        mock_session.side_effect = Exception("Database connection failed")

        response = client.get("/health/ready")
        assert response.status_code == 503
        assert response.json()["status"] == "not ready"

    def test_comprehensive_health_includes_all_checks(self, client):
        """Health endpoint should check all dependencies"""
        response = client.get("/health")
        data = response.json()

        assert response.status_code == 200
        assert "status" in data
        assert "timestamp" in data
        assert "checks" in data
        assert "database" in data["checks"]

    def test_metrics_endpoint_returns_prometheus_format(self, client):
        """Metrics endpoint should return Prometheus format"""
        response = client.get("/metrics")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        assert "http_requests_total" in response.text
        assert "http_request_duration_seconds" in response.text
