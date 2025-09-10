import time

import pytest

from app.services.circuit_breaker import CircuitBreaker, CircuitState


class TestCircuitBreaker:
    """Test resilience patterns"""

    def test_circuit_breaker_closes_after_success(self):
        """Circuit should remain closed with successful calls"""
        breaker = CircuitBreaker("test", failure_threshold=3)

        def success_func():
            return "success"

        # Multiple successful calls
        for _ in range(5):
            result = breaker.call(success_func)
            assert result == "success"

        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0

    def test_circuit_breaker_opens_after_failures(self):
        """Circuit should open after threshold failures"""
        breaker = CircuitBreaker("test", failure_threshold=3)

        def failing_func():
            raise Exception("Service unavailable")

        # Fail until threshold
        for _i in range(3):
            with pytest.raises(Exception):
                breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN
        assert breaker.failure_count == 3

        # Next call should fail fast
        with pytest.raises(Exception) as exc_info:
            breaker.call(failing_func)
        assert "Circuit breaker test is OPEN" in str(exc_info.value)

    def test_circuit_breaker_half_open_recovery(self):
        """Circuit should try half-open after timeout"""
        breaker = CircuitBreaker("test", failure_threshold=2, timeout=1)

        def intermittent_func():
            if breaker.state == CircuitState.HALF_OPEN:
                return "recovered"
            raise Exception("Still failing")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                breaker.call(intermittent_func)

        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(1.1)

        # Should try half-open
        result = breaker.call(intermittent_func)
        assert result == "recovered"
        assert breaker.state == CircuitState.CLOSED
