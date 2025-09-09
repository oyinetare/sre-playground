from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.db.database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    student_id = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    grade = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
