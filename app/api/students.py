import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.metrics import students_created_total
from app.db.database import get_db
from app.models.student import Student
from app.services.audit_service import audit_service
from app.services.external_service import external_grade_service
from app.services.sqs_service import sqs_service

router = APIRouter()


# Pydantic models
class StudentCreate(BaseModel):
    first_name: str
    last_name: str
    grade: int


class StudentResponse(BaseModel):
    id: int
    student_id: str
    first_name: str
    last_name: str
    grade: int
    created_at: datetime


@router.post("/students", response_model=StudentResponse)
async def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    """Create a new student"""
    # logger.info(
    #     "Admin creating student",
    #     extra={"admin": current_user["username"]}
    # )

    # if feature_flags.is_enabled(FeatureFlag.EMAIL_NOTIFICATIONS, student.student_id):
    #     # Send welcome email
    #     await send_welcome_email(student)

    db_student = Student(
        student_id=f"STU-{uuid.uuid4().hex[:8].upper()}",
        first_name=student.first_name,
        last_name=student.last_name,
        grade=student.grade,
    )

    db.add(db_student)
    db.commit()
    db.refresh(db_student)

    # update metrics
    students_created_total.inc()

    # send event (don't fail if SQS is down)
    sqs_service.send_event(
        "student_created",
        {
            "student_id": db_student.student_id,
            "name": f"{db_student.first_name} {db_student.last_name}",
            "grade": db_student.grade,
        },
    )

    audit_service.log_action(
        "student_created",
        {"student_id": db_student.student_id, "created_by": "api_user"},
    )

    return db_student


@router.get("/students", response_model=list[StudentResponse])
async def list_students(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all students"""
    # logger.info("User listing students", extra={"user": current_user["username"]})
    students = db.query(Student).offset(skip).limit(limit).all()
    return students


@router.get("/students/{student_id}", response_model=StudentResponse)
def get_student(student_id: str, db: Session = Depends(get_db)):
    """Get a specific student"""
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.get("/students/{student_id}/grades")
def get_student_grades(student_id: str):
    """Get grades from external service with circuit breaker"""
    return external_grade_service.get_grades(student_id)


# @router.get("/api/v1/features")
# async def get_my_features(current_user: dict = Depends(get_current_user)):
#     """Get feature flags for current user"""
#     return feature_flags.get_all_flags(current_user["username"])
