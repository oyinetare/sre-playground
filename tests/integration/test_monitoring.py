from prometheus_client.parser import text_string_to_metric_families


class TestMonitoringIntegration:
    """Test monitoring and metrics integration"""

    def test_metrics_increase_with_requests(self, client):
        """Metrics should track API usage"""
        # Get initial metrics
        initial_metrics = client.get("/metrics")
        initial_request_count = self._get_metric_value(
            initial_metrics.text, "http_requests_total"
        )

        # Make some requests
        for _ in range(5):
            client.get("/health")
            client.get("/api/v1/students")

        # Get updated metrics
        updated_metrics = client.get("/metrics")
        updated_request_count = self._get_metric_value(
            updated_metrics.text, "http_requests_total"
        )

        # Should have increased by at least 10 (5 health + 5 students)
        assert updated_request_count >= initial_request_count + 10

    def test_student_creation_updates_business_metrics(self, client):
        """Business metrics should track student creation"""
        # Get initial count
        initial_metrics = client.get("/metrics")
        initial_students = self._get_metric_value(
            initial_metrics.text, "students_created_total", default=0
        )

        # Create students
        for i in range(3):
            client.post(
                "/api/v1/students",
                json={"first_name": f"Metric{i}", "last_name": "Test", "grade": 8},
            )

        # Check metrics
        updated_metrics = client.get("/metrics")
        updated_students = self._get_metric_value(
            updated_metrics.text, "students_created_total"
        )

        assert updated_students == initial_students + 3

    def test_error_responses_tracked_in_metrics(self, client):
        """Error responses should be tracked separately"""
        # Cause some errors
        for _ in range(3):
            client.post("/api/v1/students", json={"invalid": "data"})
            client.get("/api/v1/students/INVALID-ID")

        # Check metrics
        metrics_response = client.get("/metrics")
        metrics_text = metrics_response.text

        # Should have 4xx errors tracked
        assert 'status="422"' in metrics_text or 'status="404"' in metrics_text

    def _get_metric_value(self, metrics_text, metric_name, default=0):
        """Helper to extract metric value from Prometheus format"""
        for family in text_string_to_metric_families(metrics_text):
            if family.name == metric_name:
                for sample in family.samples:
                    if sample[0] == metric_name:
                        return sample[2]
        return default
