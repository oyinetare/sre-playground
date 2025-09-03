from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
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