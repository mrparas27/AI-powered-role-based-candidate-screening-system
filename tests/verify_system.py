import io
import json
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import SessionLocal, KnowledgeChunkModel

# Create an in-memory client for testing the live app routes
client = TestClient(app)

def test_full_pipeline():
    print("==================================================")
    print("   Running Evaluator.AI End-to-End System Tests   ")
    print("==================================================")

    # 1. Verify Seeding Check
    print("\n[Test 1] Checking Vector Database Status...")
    res = client.get("/api/admin/status")
    assert res.status_code == 200, f"Status check failed: {res.text}"
    counts = res.json()["knowledge_base_counts"]
    print(f"-> Seeded knowledge base sizes: AI/ML={counts.get('ai_ml')}, Data Science={counts.get('data_science')}, Backend={counts.get('backend')}")
    assert counts["ai_ml"] > 0 or counts["backend"] > 0, "No chunks seeded. Run seed script first."

    # 2. Upload Mock Resume
    print("\n[Test 2] Testing Resume Upload & Extraction...")
    mock_pdf_content = b"%PDF-1.4 Mock PDF Content with Skills: Python, SQL, REST APIs, FastAPI, Machine Learning, Decision Trees."
    
    # We send Form data
    response = client.post(
        "/api/resume/upload",
        data={
            "name": "Jane Doe",
            "email": "jane.doe@example.com",
            "role": "ai_ml"
        },
        files={
            "file": ("jane_resume.txt", io.BytesIO(mock_pdf_content), "text/plain")
        }
    )
    
    assert response.status_code == 200, f"Resume upload failed: {response.text}"
    session_data = response.json()
    session_id = session_data["session_id"]
    extracted = session_data["extracted_skills"]
    print(f"-> Session registered: {session_id}")
    print(f"-> Extracted skills: {extracted.get('skills')}")
    print(f"-> Extracted technologies: {extracted.get('technologies')}")
    print(f"-> Experience summary: {extracted.get('experience_summary')}")
    assert session_id is not None
    assert len(extracted.get("skills", [])) > 0

    # 3. Start Interview
    print("\n[Test 3] Testing Interview Initialization...")
    response = client.post(
        "/api/interview/start",
        json={"session_id": session_id}
    )
    assert response.status_code == 200, f"Interview start failed: {response.text}"
    start_data = response.json()
    print(f"-> Q1 Number: {start_data['question_number']}")
    print(f"-> Q1 Text: {start_data['question_text']}")
    assert start_data["question_number"] == 1
    assert len(start_data["question_text"]) > 10

    # 4. Answer Questions (1 to 5)
    print("\n[Test 4] Simulating 5-Question Interview Loop...")
    
    answers = [
        "Supervised learning trains on labeled data, whereas unsupervised learning finds hidden structures in unlabeled data.",
        "Gradient descent updates weights by subtracting the gradient of the cost function scaled by a learning rate.",
        "Regularization like L1 and L2 add penalties to the loss function to constrain weight sizes and prevent overfitting.",
        "Decision trees split nodes using entropy to maximize Information Gain or Gini index to get pure subsets.",
        "The bias-variance tradeoff is the conflict between modeling complexity and generalization; bagging reduces variance."
    ]
    
    for i in range(1, 6):
        print(f"\n-> Answering Question #{i}...")
        ans_text = answers[i-1]
        
        response = client.post(
            "/api/interview/answer",
            json={
                "session_id": session_id,
                "answer": ans_text
            }
        )
        assert response.status_code == 200, f"Submit answer failed: {response.text}"
        ans_data = response.json()
        
        # Verify grading response
        evaluation = ans_data["evaluation"]
        print(f"   Score Assigned: {evaluation['score']}/10")
        print(f"   AI Feedback: {evaluation['feedback']}")
        print(f"   Concept Traceability: {evaluation['traceability']}")
        
        if i < 5:
            assert ans_data["finished"] is False
            print(f"   Next Question #{ans_data['next_question_number']}: {ans_data['next_question_text']}")
        else:
            assert ans_data["finished"] is True
            print("-> Assessment Finished!")
            report = ans_data["report"]
            print(f"\n[Test 5] Checking Final Evaluation Summary...")
            print(f"-> Hiring Verdict: {report.get('verdict')}")
            print(f"-> Overall Score: {report.get('overall_score')}%")
            print(f"-> Competencies: {report.get('competencies')}")
            print(f"-> Strengths: {report.get('strengths')}")
            print(f"-> Improvements Needed: {report.get('improvements')}")
            print(f"-> Final Summary: {report.get('summary')}")
            
            assert report["overall_score"] >= 0.0
            assert report["verdict"] in ['Strongly Recommend', 'Recommend', 'Borderline', 'Do Not Recommend']

    # 5. Get Session details
    print("\n[Test 6] Testing Interview Session History GET Route...")
    response = client.get(f"/api/interview/session/{session_id}")
    assert response.status_code == 200
    details = response.json()
    assert details["status"] == "completed"
    assert len(details["qa_history"]) == 5
    print("-> GET session history successfully verified. Contains 5 completed QA records.")

    print("\n==================================================")
    print("      ALL END-TO-END SYSTEM TESTS PASSED!       ")
    print("==================================================")

if __name__ == "__main__":
    test_full_pipeline()
