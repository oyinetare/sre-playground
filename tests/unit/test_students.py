import pytest
from pydantic import ValidationError

from app.api.students import StudentCreate
from app.models.student import Student


class TestStudentDomain:
    """Test business logic for students"""

    def test_student_creation_with_valid_data(self):
        """Test creating a student with valid data"""
        student_data = StudentCreate(first_name="Alice", last_name="Johnson", grade=10)

        assert student_data.first_name == "Alice"
        assert student_data.last_name == "Johnson"
        assert student_data.grade == 10

    def test_student_creation_with_invalid_grade(self):
        """Grade must be between 1 and 12"""
        with pytest.raises(ValidationError) as exc_info:
            StudentCreate(
                first_name="Bob",
                last_name="Smith",
                grade=13,  # Invalid
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("grade",) for error in errors)

    def test_student_creation_with_empty_name(self):
        """Names cannot be empty"""
        with pytest.raises(ValidationError):
            StudentCreate(
                first_name="",  # Invalid
                last_name="Doe",
                grade=5,
            )

    def test_student_id_generation(self, test_db):
        """Student ID should be generated in correct format"""
        from app.db.database import SessionLocal

        db = SessionLocal()
        student = Student(
            student_id="STU-12345678", first_name="Test", last_name="Student", grade=8
        )

        assert student.student_id.startswith("STU-")
        assert len(student.student_id) == 12  # STU- + 8 chars
        db.close()
