import json
from sqlalchemy.orm import Session
from openai import OpenAI
from backend.app.config import OPENAI_API_KEY
from backend.app.db import SessionModel, QARecordModel
from backend.app.rag import retrieve_context

def get_openai_client():
    return OpenAI(api_key=OPENAI_API_KEY)

def generate_next_question(db: Session, session_id: str) -> dict:
    """Generates the next interview question based on resume, role, retrieved context, and past Q&A."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise ValueError("Session not found")
        
    role = session.target_role
    resume_info = json.loads(session.extracted_skills) if session.extracted_skills else {}
    
    # Load completed QA history
    history = db.query(QARecordModel).filter(
        QARecordModel.session_id == session_id
    ).order_by(QARecordModel.question_number.asc()).all()
    
    num_questions_asked = len(history)
    current_q_num = num_questions_asked + 1
    
    # Determine the theme for this question to ensure a structured progression:
    # Q1: Warm-up & Core Skill Integration
    # Q2: Algorithmic / Deep Technical Dive
    # Q3: Practical System / Scenario-based Application
    # Q4: Troubleshooting, Edge Cases, or Optimization
    # Q5: Fundamental Theory & Math Check
    themes = {
        1: "Warm-up / Core Concepts (Checking major skills highlighted in resume)",
        2: "Deep Technical / Algorithmic Dive (Detailed theoretical or structural details)",
        3: "Applied Engineering / Practical Scenario (Building/solving a real-world problem)",
        4: "Edge cases, Debugging, and Optimization (Grilling on performance limits or common traps)",
        5: "Fundamental Principles / Math check (Verifying the absolute bedrock core theory)"
    }
    current_theme = themes.get(current_q_num, "General Interview Question")
    
    # Dynamic Query construction for RAG based on theme, resume skills, and past performance
    skills_list = resume_info.get("skills", ["Machine Learning", "Software Development"])
    tech_list = resume_info.get("technologies", ["Python"])
    
    # Build query keywords
    query_keywords = []
    if current_q_num == 1:
        query_keywords = [skills_list[0] if skills_list else "Machine Learning"]
    elif current_q_num == 2:
        query_keywords = [skills_list[min(1, len(skills_list)-1)] if len(skills_list) > 1 else "Algorithms"]
    elif current_q_num == 3:
        query_keywords = ["applied " + (tech_list[0] if tech_list else "coding")]
    elif current_q_num == 4:
        query_keywords = ["optimization", "gradient descent", "concurrency", "indexing"]
    else:
        query_keywords = ["theory", "concepts", "math"]
        
    rag_query = f"{' '.join(query_keywords)} {role}"
    
    # Retrieve relevant book chunks (RAG)
    # Mapping roles to textbook types in database
    role_mapping = {
        "ai_ml": "ai_ml",
        "data_science": "data_science",
        "backend": "backend"
    }
    db_role = role_mapping.get(role, "ai_ml")
    
    retrieved_results = retrieve_context(db, rag_query, db_role, limit=3)
    retrieved_context_text = "\n\n".join([f"Source [{r['file_name']}]: {r['chunk_text']}" for r in retrieved_results])
    
    # Build history context
    history_context = ""
    avg_score = 5.0
    if history:
        history_context = "Here is what has happened so far in this interview:\n"
        scores = []
        for i, h in enumerate(history):
            history_context += f"Q{h.question_number}: {h.question_text}\nCandidate Answer: {h.candidate_answer or 'No answer'}\nFeedback: {h.evaluation_feedback or ''}\nScore: {h.evaluation_score or 0}/10\n\n"
            if h.evaluation_score is not None:
                scores.append(h.evaluation_score)
        if scores:
            avg_score = sum(scores) / len(scores)

    # Determine adaptive difficulty
    difficulty = "Moderate"
    if len(history) > 0:
        if avg_score >= 8.0:
            difficulty = "Challenging (Candidate is doing great, push them further)"
        elif avg_score < 5.0:
            difficulty = "Fundamental (Candidate is struggling, verify basic concepts)"
            
    system_prompt = (
        "You are an expert technical interviewer conducting a live structured interview for the role: {role}.\n"
        "Your task is to generate the NEXT question (Question #{q_num}) for the candidate.\n\n"
        "Rules:\n"
        "1. GROUND the question in the provided Textbook Context below. Do not test random things outside this content.\n"
        "2. INFLUENCE the question using the candidate's resume summary: {experience_summary}.\n"
        "3. Follow this specific theme: {theme}.\n"
        "4. Set difficulty level to: {difficulty}.\n"
        "5. Avoid simple template questions. Keep it technical, engaging, and professional.\n"
        "6. Do not ask double-barreled questions (e.g. 'What is X and why is Y and how is Z?'). Ask ONE clear question.\n"
        "7. Respond ONLY in valid JSON format matching the following keys:\n"
        "   - 'question': The interview question to ask.\n"
        "   - 'evaluation_criteria': What conceptual/applied points a good answer must address.\n"
        "   - 'retrieved_context_summary': A 1-sentence summary of the textbook context used.\n"
    ).format(
        role=role.upper(),
        q_num=current_q_num,
        experience_summary=resume_info.get("experience_summary", ""),
        theme=current_theme,
        difficulty=difficulty
    )

    user_prompt = (
        "--- Textbook Context (RAG) ---\n"
        "{context}\n\n"
        "--- Interview History ---\n"
        "{history_context}\n\n"
        "Generate Question #{q_num} matching the theme: {theme}."
    ).format(
        context=retrieved_context_text if retrieved_context_text else "No specific textbook context found.",
        history_context=history_context if history_context else "Interview just started.",
        q_num=current_q_num,
        theme=current_theme
    )

    # High-quality fallback questions for API failures/limits
    fallback_questions = {
        "ai_ml": [
            "What is the difference between supervised and unsupervised learning, and how would you select a loss function for binary classification?",
            "Can you explain how Gradient Descent works and why normalizing features is important before training?",
            "What is overfitting, and how do regularizations like L1 (Lasso) and L2 (Ridge) prevent it?",
            "Explain the architecture of a simple Decision Tree and what metrics are used to split a node.",
            "How does the Bias-Variance tradeoff affect machine learning models, and how do ensemble methods like Random Forests help?"
        ],
        "data_science": [
            "Explain the concept of K-Fold Cross-Validation and how it helps prevent data leakage during hyperparameter tuning.",
            "What is the difference between standard scaling (StandardScaler) and min-max scaling (MinMaxScaler), and when is each preferred?",
            "What is ROC AUC, and how does it compare to F1-Score as an evaluation metric for imbalanced classification tasks?",
            "How does the Naive Bayes classifier compute predictions, and what is the significance of the conditional independence assumption?",
            "Explain how the bagging ensemble technique reduces model variance and contrast it with boosting which reduces bias."
        ],
        "backend": [
            "What is the difference between SQL and NoSQL databases, and when would you choose one over the other?",
            "Explain the concept of database indexing. How does an index speed up queries, and what are the write overheads?",
            "How do you design a RESTful API? What HTTP methods and status codes would you use for creating, reading, and updating resources?",
            "What is database normalization? Explain 1NF, 2NF, and 3NF with a simple practical example.",
            "Describe how you would handle race conditions in a multi-threaded backend application using locks or transactions."
        ]
    }
    fallback_list = fallback_questions.get(db_role, fallback_questions["ai_ml"])
    q_idx = min(num_questions_asked, len(fallback_list) - 1)

    if not OPENAI_API_KEY:
        return {
            "question": fallback_list[q_idx],
            "evaluation_criteria": "Verify core engineering principles.",
            "retrieved_context_summary": "Seeded core knowledge."
        }

    client = get_openai_client()
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error generating question: {e}")
        return {
            "question": fallback_list[q_idx],
            "evaluation_criteria": "Verify core engineering principles under fallback mode.",
            "retrieved_context_summary": "Standard textbook-grounded backup concept."
        }

def evaluate_candidate_answer(db: Session, session_id: str, answer_text: str) -> dict:
    """Evaluates the candidate's latest answer against the question criteria and textbook context."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise ValueError("Session not found")
        
    current_q_num = session.current_question_number
    
    # Get active question record
    qa_record = db.query(QARecordModel).filter(
        QARecordModel.session_id == session_id,
        QARecordModel.question_number == current_q_num
    ).first()
    
    if not qa_record:
        raise ValueError(f"QA Record for question #{current_q_num} not found")
        
    system_prompt = (
        "You are a technical examiner grading a candidate's answer during an interview.\n"
        "Assess the candidate's answer based on correctness, technical depth, and alignment with technical textbook concepts.\n\n"
        "Evaluate the response and output a JSON object containing:\n"
        "- 'score': A float between 0.0 and 10.0.\n"
        "- 'feedback': Constructive feedback describing what was correct, what was missing, and what could be improved.\n"
        "- 'traceability': A short sentence mapping their answer to the evaluated concept (e.g., 'Evaluated their explanation of gradient updates against Bishop's PRML definitions')."
    )
    
    user_prompt = (
        "--- Question Asked ---\n"
        "{question}\n\n"
        "--- Textbook Context References ---\n"
        "{context}\n\n"
        "--- Candidate's Answer ---\n"
        "{answer}\n\n"
        "Grade this answer."
    ).format(
        question=qa_record.question_text,
        context=qa_record.context_retrieved if qa_record.context_retrieved else "N/A",
        answer=answer_text
    )
    
    if not OPENAI_API_KEY:
        # Fallback evaluation
        score = 7.0 if len(answer_text.split()) > 15 else 4.0
        return {
            "score": score,
            "feedback": "Answer analyzed using fallback evaluator. Good effort; expand more on theoretical aspects.",
            "traceability": "Mapped against core concepts."
        }

    client = get_openai_client()
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error grading answer: {e}")
        return {
            "score": 6.0,
            "feedback": "Grading error occurred. Average score assigned. Make sure technical terms are used.",
            "traceability": "General matching."
        }

def generate_final_report(db: Session, session_id: str) -> dict:
    """Compiles all QA records for a session and outputs a final analytical evaluation report."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise ValueError("Session not found")
        
    qa_records = db.query(QARecordModel).filter(
        QARecordModel.session_id == session_id
    ).order_by(QARecordModel.question_number.asc()).all()
    
    if not qa_records:
        return {
            "overall_score": 0.0,
            "verdict": "No evaluation possible (No questions answered)",
            "competencies": {},
            "strengths": [],
            "improvements": [],
            "summary": "The candidate did not answer any questions."
        }
        
    # Calculate average score
    scores = [r.evaluation_score for r in qa_records if r.evaluation_score is not None]
    overall_avg = sum(scores) / len(scores) if scores else 0.0
    
    # Build list of Q&As for LLM review
    qa_history_str = ""
    for r in qa_records:
        qa_history_str += (
            f"Question {r.question_number}: {r.question_text}\n"
            f"Candidate Answer: {r.candidate_answer}\n"
            f"Examiner Score: {r.evaluation_score}/10\n"
            f"Examiner Feedback: {r.evaluation_feedback}\n\n"
        )
        
    system_prompt = (
        "You are a principal technical engineer compiling a final hiring review for a candidate after a 5-question technical assessment.\n"
        "Generate a structured review based on their answers, scores, and feedback.\n"
        "Return ONLY a JSON object containing:\n"
        "- 'verdict': One of ['Strongly Recommend', 'Recommend', 'Borderline', 'Do Not Recommend']\n"
        "- 'competencies': A dictionary where keys are competencies (e.g. 'Theoretical Foundations', 'Applied Scenarios', 'Problem Solving', 'Communication') "
        "and values are integers between 0 and 100.\n"
        "- 'strengths': List of 2-3 specific technical strengths demonstrated.\n"
        "- 'improvements': List of 2-3 specific topics/skills they need to work on.\n"
        "- 'summary': A 3-4 sentence comprehensive final assessment outlining their suitability for the role."
    )
    
    user_prompt = (
        "Candidate Name: {name}\n"
        "Target Role: {role}\n"
        "Average Score: {avg_score:.2f}/10\n\n"
        "--- Interview Q&A History ---\n"
        "{history}\n\n"
        "Synthesize this into the final hiring review JSON."
    ).format(
        name=session.candidate_name,
        role=session.target_role,
        avg_score=overall_avg,
        history=qa_history_str
    )
    
    if not OPENAI_API_KEY:
        # Fallback final report
        verdict = "Recommend" if overall_avg >= 7.0 else "Borderline"
        return {
            "overall_score": float(round(overall_avg * 10, 1)),
            "verdict": verdict,
            "competencies": {
                "Theoretical Foundations": int(overall_avg * 10),
                "Applied Scenarios": int(overall_avg * 9),
                "Problem Solving": int(overall_avg * 10),
                "Communication": 80
            },
            "strengths": ["Clear communication", "Addresses core questions"],
            "improvements": ["Could benefit from deep theoretical references"],
            "summary": f"The candidate showed solid performance across questions with an average score of {overall_avg:.1f}/10. Meets the criteria."
        }

    client = get_openai_client()
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )
        report = json.loads(response.choices[0].message.content)
        report["overall_score"] = float(round(overall_avg * 10, 1))
        return report
    except Exception as e:
        print(f"Error compiling final report: {e}")
        return {
            "overall_score": float(round(overall_avg * 10, 1)),
            "verdict": "Borderline",
            "competencies": {
                "Core Engineering": int(overall_avg * 10),
                "Systems / Algorithms": int(overall_avg * 9)
            },
            "strengths": ["Capable of writing functional answers"],
            "improvements": ["Needs to expand on technical edges"],
            "summary": "Synthesized review failed due to AI service timeout. Raw score is sufficient."
        }
