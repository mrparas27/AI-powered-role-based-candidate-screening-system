import json
from datetime import datetime
import uuid
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, ForeignKey, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from backend.app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class SessionModel(Base):
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_name = Column(String(100), nullable=False)
    candidate_email = Column(String(100), nullable=False)
    target_role = Column(String(50), nullable=False) # ai_ml, data_science, backend
    resume_text = Column(Text, nullable=True)
    extracted_skills = Column(Text, nullable=True)  # JSON string containing skills, technologies, experience
    current_question_number = Column(Integer, default=0)
    status = Column(String(20), default="pending")  # pending, interviewing, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    evaluation_report = Column(Text, nullable=True)  # JSON string containing final performance audit
    
    qa_records = relationship("QARecordModel", back_populates="session", cascade="all, delete-orphan")

class QARecordModel(Base):
    __tablename__ = "qa_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    question_number = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    context_retrieved = Column(Text, nullable=True)
    candidate_answer = Column(Text, nullable=True)
    evaluation_score = Column(Float, nullable=True)
    evaluation_feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("SessionModel", back_populates="qa_records")

class KnowledgeChunkModel(Base):
    __tablename__ = "knowledge_base"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    chunk_text = Column(Text, nullable=False)
    file_name = Column(String(150), nullable=False)
    role_type = Column(String(50), nullable=False)  # ai_ml, data_science, backend
    embedding = Column(LargeBinary, nullable=False)  # float32 array stored as binary blob
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
