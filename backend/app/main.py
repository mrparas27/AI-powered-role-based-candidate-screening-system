import json
from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend.app.db import get_db, init_db, SessionModel, QARecordModel, KnowledgeChunkModel
from backend.app.parser import extract_text_from_pdf, parse_resume_content
from backend.app.rag import ingest_document
from backend.app.llm import generate_next_question, evaluate_candidate_answer, generate_final_report

app = FastAPI(title="AI-Powered Role-Based Candidate Screening System API")

# Configure CORS so React frontend can connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual frontend origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    # Initialize SQLite database schema
    init_db()

@app.post("/api/resume/upload")
async def upload_resume(
    name: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),  # ai_ml, data_science, backend
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Parses candidate resume, extracts skills, and registers session."""
    # 1. Read file bytes
    file_bytes = await file.read()
    filename = file.filename
    
    # 2. Extract raw text based on file format
    if filename.endswith(".pdf"):
        resume_text = extract_text_from_pdf(file_bytes)
    else:
        # Fallback to plain text
        resume_text = file_bytes.decode("utf-8", errors="ignore")
        
    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Unable to extract text from the uploaded file.")
        
    # 3. Parse resume with LLM
    extracted_data = parse_resume_content(resume_text)
    
    # 4. Create new interview session
    session = SessionModel(
        candidate_name=name,
        candidate_email=email,
        target_role=role,
        resume_text=resume_text,
        extracted_skills=json.dumps(extracted_data),
        status="pending",
        current_question_number=0
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return {
        "session_id": session.id,
        "candidate": {
            "name": session.candidate_name,
            "email": session.candidate_email,
            "role": session.target_role
        },
        "extracted_skills": extracted_data
    }

@app.post("/api/interview/start")
def start_interview(payload: dict, db: Session = Depends(get_db)):
    """Starts the interview, generating the first question."""
    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
        
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session.status != "pending":
        raise HTTPException(status_code=400, detail="Interview has already started or completed.")
        
    # Set status and generate Q1
    session.status = "interviewing"
    session.current_question_number = 1
    
    q_data = generate_next_question(db, session_id)
    
    # Create Q1 record
    qa_record = QARecordModel(
        session_id=session.id,
        question_number=1,
        question_text=q_data["question"],
        context_retrieved=q_data.get("retrieved_context_summary", "")
    )
    
    db.add(qa_record)
    db.commit()
    
    return {
        "session_id": session.id,
        "question_number": 1,
        "question_text": q_data["question"]
    }

@app.post("/api/interview/answer")
def submit_answer(payload: dict, db: Session = Depends(get_db)):
    """Submits answer to current question, grades it, and proceeds to next question or finishes."""
    session_id = payload.get("session_id")
    answer = payload.get("answer")
    
    if not session_id or answer is None:
        raise HTTPException(status_code=400, detail="session_id and answer are required")
        
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session.status != "interviewing":
        raise HTTPException(status_code=400, detail="Interview is not active.")
        
    current_q_num = session.current_question_number
    
    # 1. Grade current answer
    evaluation = evaluate_candidate_answer(db, session_id, answer)
    
    # 2. Update current QA record
    qa_record = db.query(QARecordModel).filter(
        QARecordModel.session_id == session_id,
        QARecordModel.question_number == current_q_num
    ).first()
    
    if not qa_record:
         raise HTTPException(status_code=404, detail="Current question record not found.")
         
    qa_record.candidate_answer = answer
    qa_record.evaluation_score = evaluation["score"]
    qa_record.evaluation_feedback = evaluation["feedback"]
    
    db.commit()
    
    # 3. Check if interview is finished (5 questions max)
    if current_q_num >= 5:
        # Generate final review
        report = generate_final_report(db, session_id)
        
        session.status = "completed"
        session.evaluation_report = json.dumps(report)
        db.commit()
        
        return {
            "finished": True,
            "evaluation": evaluation,
            "report": report
        }
    else:
        # Generate next question
        next_q_num = current_q_num + 1
        
        # Increment session current question number first so RAG query logic sees updated state
        session.current_question_number = next_q_num
        db.commit()
        
        q_data = generate_next_question(db, session_id)
        
        # Create next QA record
        next_qa_record = QARecordModel(
            session_id=session.id,
            question_number=next_q_num,
            question_text=q_data["question"],
            context_retrieved=q_data.get("retrieved_context_summary", "")
        )
        db.add(next_qa_record)
        db.commit()
        
        return {
            "finished": False,
            "evaluation": evaluation,
            "next_question_number": next_q_num,
            "next_question_text": q_data["question"]
        }

@app.get("/api/interview/session/{session_id}")
def get_session_details(session_id: str, db: Session = Depends(get_db)):
    """Fetches details, QA history, and final evaluation report of a session."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    qa_history = db.query(QARecordModel).filter(
        QARecordModel.session_id == session_id
    ).order_by(QARecordModel.question_number.asc()).all()
    
    history_list = []
    for qa in qa_history:
        history_list.append({
            "question_number": qa.question_number,
            "question_text": qa.question_text,
            "candidate_answer": qa.candidate_answer,
            "evaluation_score": qa.evaluation_score,
            "evaluation_feedback": qa.evaluation_feedback,
            "context_retrieved": qa.context_retrieved
        })
        
    report_data = None
    if session.evaluation_report:
        report_data = json.loads(session.evaluation_report)
        
    return {
        "session_id": session.id,
        "candidate_name": session.candidate_name,
        "candidate_email": session.candidate_email,
        "target_role": session.target_role,
        "status": session.status,
        "current_question_number": session.current_question_number,
        "extracted_skills": json.loads(session.extracted_skills) if session.extracted_skills else None,
        "created_at": session.created_at,
        "qa_history": history_list,
        "evaluation_report": report_data
    }

@app.post("/api/admin/ingest")
async def admin_ingest(
    role_type: str = Form(...),  # ai_ml, data_science, backend
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Endpoint for uploading and chunking/embedding textbook documents."""
    file_bytes = await file.read()
    filename = file.filename
    
    if filename.endswith(".pdf"):
        text = extract_text_from_pdf(file_bytes)
    else:
        text = file_bytes.decode("utf-8", errors="ignore")
        
    if not text.strip():
        raise HTTPException(status_code=400, detail="Document contains no text.")
        
    chunks_created = ingest_document(db, text, filename, role_type)
    
    return {
        "message": f"Successfully ingested {filename}",
        "role_type": role_type,
        "chunks_created": chunks_created
    }

@app.get("/api/admin/status")
def admin_status(db: Session = Depends(get_db)):
    """Returns the size and counts of the vector knowledge base database."""
    counts = {}
    for role in ["ai_ml", "data_science", "backend"]:
        cnt = db.query(KnowledgeChunkModel).filter(KnowledgeChunkModel.role_type == role).count()
        counts[role] = cnt
    return {
        "knowledge_base_counts": counts
    }
