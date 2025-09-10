from app.services.circuit_breaker import CircuitBreaker

class ExternalGradeService:
    def __init__(self):
        self.circuit_breaker = CircuitBreaker("grade_service")

    def get_grades(self, student_id: str):
        try:
            return self.circuit_breaker.call(self._fetch_from_external_api, student_id)
        except:
            # return cached/default data
            return {"grades": [], "cached": True}

    def _fetch_from_external_api(self, student_id: str):
        # simulate external API call
        import random
        if random.random() < 0.3:  # 30% failure rate for demo
            raise Exception("External API error")
        return {"grades": ["A", "B+", "A-"], "cached": False}