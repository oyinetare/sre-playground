from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime
import uuid

from app.db.database import get_db
from app.models.student import Student

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
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    """Create a new student"""
    db_student = Student(
        student_id=f"STU-{uuid.uuid4().hex[:8].upper()}",
        first_name=student.first_name,
        last_name=student.last_name,
        grade=student.grade
    )

    db.add(db_student)
    db.commit()
    db.refresh(db_student)

    return db_student

@router.get("/students", response_model=List[StudentResponse])
def list_students(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all students"""
    students = db.query(Student).offset(skip).limit(limit).all()
    return students

@router.get("/students/{student_id}", response_model=StudentResponse)
def get_student(student_id: str, db: Session = Depends(get_db)):
    """Get a specific student"""
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student