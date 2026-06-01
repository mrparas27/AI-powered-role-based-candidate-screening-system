# Evaluator.AI: Role-Based Candidate Screening System

Evaluator.AI is an intelligent, retrieval-augmented technical screening system designed to evaluate candidate proficiency dynamically based on their resume profile and reference textbooks.

---

## 🌟 Key Features

1. **Structured Candidate Onboarding**: Capture candidate metadata (Name, Email, Target Role) and support drag-and-drop resume upload.
2. **Textbook-Grounded RAG (Retrieval-Augmented Generation)**: Core questions are matched against vector embeddings of fundamental literature:
   - **AI/ML**: Tom Mitchell's *Machine Learning*, Burkov's *The Hundred-Page Machine Learning Book*.
   - **Data Science**: Andreas Müller's *Introduction to Machine Learning*, Jason Brownlee's *Basics of Linear Algebra*.
   - **Backend Systems**: REST APIs, database scaling, transaction locks, and ACID principles.
3. **Adaptive 5-Level Questioning**:
   - *Level 1*: Foundation Warm-up
   - *Level 2*: Deep Dive (Algorithms / Design)
   - *Level 3*: Practical Application (Architecture Scenario)
   - *Level 4*: Edge Cases & Scale Optimization
   - *Level 5*: Foundational Theory (Math, Proofs)
4. **Immediate Answer Evaluation**: Candidates receive instantaneous scoring (0-10), technical critique, and citation tracking after submitting each response.
5. **Interactive Hiring Dashboard**: Review overall scores, executive hiring verdicts (`Strongly Recommend`, `Recommend`, `Borderline`, `Do Not Recommend`), custom competency progress bar maps, and detailed chronologies of the question log.
6. **Graceful Fallbacks**: Fully operational under API limits or credential failures. Uses local parsing heuristical backups and structured fallback progression indexes to complete the flow without crashing.

---

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python 3.10+), SQLAlchemy (SQLite Database), PyPDF2 (Resume Text Extractor), OpenAI API (gpt-4o-mini & embeddings).
- **Vector Search Engine**: Embedded NumPy cosine similarity (`np.dot`) comparing floats loaded from binary DB columns (no heavy external database installation needed).
- **Frontend**: React (Vite, JavaScript), Vanilla CSS, Lucide Icons, responsive SVG gauges.

---

## 📂 Project Structure

```text
├── backend/
│   ├── app/
│   │   ├── config.py         # App directories, environment variables, OpenAI init
│   │   ├── db.py             # SQLite schemas (sessions, Q&As, knowledge_base)
│   │   ├── parser.py         # PDF text extractor and GPT skills parsing fallbacks
│   │   ├── rag.py            # Word-chunking & NumPy vector similarity retriever
│   │   ├── llm.py            # Question orchestration, scoring, and report compiler
│   │   └── main.py           # FastAPI routes with CORS configuration
│   ├── requirements.txt      # Python dependencies (FastAPI, NumPy, OpenAI, etc.)
│   └── seed.py               # Database populator seeding reference chapters
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # Entry, upload, questioning, and results panels
│   │   ├── index.css         # Premium CSS dark mode, typography, glassmorphism
│   │   └── main.jsx          # React app DOM loader
│   ├── index.html            # App shell with SEO titles
│   └── package.json          # Node dependencies (Vite, React, Lucide)
├── tests/
│   └── verify_system.py      # Automated mock end-to-end testing script
├── resume.txt                # Sample candidate profile for manual/auto testing
└── README.md                 # Project documentation (this file)
```

---

## 🚀 Execution Guide

### 1. Backend Setup & Ingestion
From the root directory, configure your environment and seed the textbook base:
```powershell
# Install packages
pip install -r backend/requirements.txt

# Run the seeding script to ingest reference documents
$env:PYTHONPATH="."
python backend/seed.py
```

### 2. Start the Backend Server
Start the Uvicorn web server listening on port 8000:
```powershell
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```
Interactive API docs are available at `http://127.0.0.1:8000/docs`.

### 3. Start the Frontend Application
Open a new terminal session, navigate to the `frontend` folder, install packages, and boot the server:
```powershell
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173/` in your browser.

### 4. Run Automated End-to-End Tests
Ensure the backend dependencies are configured, and run:
```powershell
$env:PYTHONPATH="."
python tests/verify_system.py
```
This tests database insertions, resume parsing fallbacks, progressive interview answers, and dashboard analytics compilation.
