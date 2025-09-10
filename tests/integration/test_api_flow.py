import pytest


class TestStudentAPIFlow:
    """Test complete API flows"""

    def test_create_and_retrieve_student(self, client):
        """Test creating a student and then retrieving it"""
        # Create student
        create_data = {"first_name": "Integration", "last_name": "Test", "grade": 11}

        create_response = client.post("/api/v1/students", json=create_data)
        assert create_response.status_code == 201

        created_student = create_response.json()
        assert created_student["first_name"] == "Integration"
        assert created_student["student_id"].startswith("STU-")

        # List students
        list_response = client.get("/api/v1/students")
        assert list_response.status_code == 200

        students = list_response.json()
        assert len(students) >= 1
        assert any(s["student_id"] == created_student["student_id"] for s in students)

    def test_create_multiple_students_generates_unique_ids(self, client):
        """Each student should get a unique ID"""
        student_ids = set()

        for i in range(5):
            response = client.post(
                "/api/v1/students",
                json={"first_name": f"Student{i}", "last_name": "Test", "grade": 10},
            )
            assert response.status_code == 201
            student_ids.add(response.json()["student_id"])

        assert len(student_ids) == 5  # All IDs should be unique

    def test_invalid_student_data_returns_422(self, client):
        """Invalid data should return validation error"""
        invalid_data = {
            "first_name": "Test",
            "last_name": "Student",
            "grade": 15,  # Invalid grade
        }

        response = client.post("/api/v1/students", json=invalid_data)
        assert response.status_code == 422

        error = response.json()
        assert "detail" in error
        assert any("grade" in str(e) for e in error["detail"])

    @pytest.mark.parametrize("grade", [1, 6, 12])
    def test_create_students_various_grades(self, client, grade):
        """Test creating students in different grades"""
        response = client.post(
            "/api/v1/students",
            json={"first_name": "Grade", "last_name": f"Test{grade}", "grade": grade},
        )

        assert response.status_code == 201
        assert response.json()["grade"] == grade
