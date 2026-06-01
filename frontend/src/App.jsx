import React, { useState } from 'react';
import { 
  User, 
  Mail, 
  Briefcase, 
  UploadCloud, 
  FileText, 
  BrainCircuit, 
  Send, 
  ChevronRight, 
  CheckCircle2, 
  HelpCircle, 
  Award, 
  TrendingUp, 
  AlertTriangle, 
  Check, 
  BookOpen,
  ArrowRight,
  RefreshCw
} from 'lucide-react';

const API_BASE = "http://localhost:8000";

function App() {
  // Navigation / Interview States
  // 'welcome' | 'parsing' | 'extracted' | 'interview' | 'grading' | 'results'
  const [step, setStep] = useState('welcome');
  
  // Form State
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('ai_ml');
  const [file, setFile] = useState(null);
  
  // API Return States
  const [sessionId, setSessionId] = useState(null);
  const [extractedSkills, setExtractedSkills] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState({ text: '', number: 0 });
  const [answer, setAnswer] = useState('');
  const [lastGrading, setLastGrading] = useState(null); // { score, feedback }
  const [evaluationReport, setEvaluationReport] = useState(null);
  const [qaHistory, setQaHistory] = useState([]);
  
  // UI Helpers
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  
  // File Drop Handlers
  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setErrorMsg('');
    }
  };

  // 1. Submit Profile & Resume for Parsing
  const startParsing = async (e) => {
    e.preventDefault();
    if (!name.trim() || !email.trim()) {
      setErrorMsg('Please enter your name and email.');
      return;
    }
    if (!file) {
      setErrorMsg('Please upload your resume (PDF or Text).');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg('');
    setStep('parsing');

    try {
      const formData = new FormData();
      formData.append('name', name);
      formData.append('email', email);
      formData.append('role', role);
      formData.append('file', file);

      const res = await fetch(`${API_BASE}/api/resume/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        throw new Error(`Failed to parse resume (Status: ${res.status})`);
      }

      const data = await res.json();
      setSessionId(data.session_id);
      setExtractedSkills(data.extracted_skills);
      setStep('extracted');
    } catch (err) {
      console.error(err);
      setErrorMsg('Error parsing resume. Please ensure the backend is running and try again.');
      setStep('welcome');
    } finally {
      setIsSubmitting(false);
    }
  };

  // 2. Start the Actual Interview Questions
  const startInterview = async () => {
    setIsSubmitting(true);
    setErrorMsg('');

    try {
      const res = await fetch(`${API_BASE}/api/interview/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });

      if (!res.ok) {
        throw new Error('Failed to start interview.');
      }

      const data = await res.json();
      setCurrentQuestion({
        text: data.question_text,
        number: data.question_number
      });
      setAnswer('');
      setLastGrading(null);
      setStep('interview');
    } catch (err) {
      console.error(err);
      setErrorMsg('Failed to fetch the first question.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // 3. Submit Answer & Show Intermediate Grade
  const submitAnswer = async () => {
    if (!answer.trim()) {
      setErrorMsg('Please type your answer before submitting.');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg('');

    try {
      const res = await fetch(`${API_BASE}/api/interview/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          answer: answer
        })
      });

      if (!res.ok) {
        throw new Error('Failed to submit answer.');
      }

      const data = await res.json();
      setLastGrading(data.evaluation);
      
      // Save current Q&A into history
      const updatedHistory = [
        ...qaHistory,
        {
          question_number: currentQuestion.number,
          question_text: currentQuestion.text,
          candidate_answer: answer,
          evaluation_score: data.evaluation.score,
          evaluation_feedback: data.evaluation.feedback
        }
      ];
      setQaHistory(updatedHistory);

      // Check if finished
      if (data.finished) {
        setEvaluationReport(data.report);
        setStep('grading'); // Shows grading first, next click leads to results
      } else {
        // Prepare next question trigger on clicking next
        setCurrentQuestion({
          text: data.next_question_text,
          number: data.next_question_number
        });
        setStep('grading');
      }
    } catch (err) {
      console.error(err);
      setErrorMsg('Failed to grade answer. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Triggered when clicking "Next Question" or "View Results" from grading panel
  const handleProceedFromGrading = () => {
    setAnswer('');
    setErrorMsg('');
    if (evaluationReport) {
      setStep('results');
    } else {
      setLastGrading(null);
      setStep('interview');
    }
  };

  // Reset Interview to Start Over
  const resetInterview = () => {
    setStep('welcome');
    setName('');
    setEmail('');
    setFile(null);
    setSessionId(null);
    setExtractedSkills(null);
    setCurrentQuestion({ text: '', number: 0 });
    setAnswer('');
    setLastGrading(null);
    setEvaluationReport(null);
    setQaHistory([]);
    setErrorMsg('');
  };

  // Text formatting helper for roles
  const getRoleLabel = (r) => {
    if (r === 'ai_ml') return 'AI / Machine Learning Engineer';
    if (r === 'data_science') return 'Data Scientist / Applied ML';
    if (r === 'backend') return 'Backend Engineer';
    return r;
  };

  return (
    <div className="app-container">
      {/* HEADER */}
      <header className="app-header">
        <div className="logo-section">
          <BrainCircuit className="logo-icon" size={32} />
          <h1 className="logo-text">Evaluator.AI</h1>
        </div>
        {sessionId && (
          <span className="role-badge">
            Role: {getRoleLabel(role)}
          </span>
        )}
      </header>

      {/* ERROR MESSAGE ALERT */}
      {errorMsg && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid #ef4444',
          color: '#f87171',
          padding: '1rem',
          borderRadius: '8px',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          animation: 'fadeIn 0.3s ease'
        }}>
          <AlertTriangle size={20} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* STEP 1: WELCOME & RESUME UPLOAD */}
      {step === 'welcome' && (
        <div className="grid-welcome">
          <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
            <h2 className="hero-title">
              Assess Technical Competence <span>Grounded in Science</span>
            </h2>
            <p className="hero-subtitle">
              Evaluator.AI generates adaptive, textbook-grounded technical questions based on your resume and selected job role, simulating an advanced recruiter evaluation.
            </p>
            
            <div className="features-list">
              <div className="feature-item">
                <div className="feature-icon-wrapper"><BookOpen size={18} /></div>
                <div className="feature-text">
                  <h4>Textbook-Grounded RAG</h4>
                  <p>Questions reference foundational chapters from Tom Mitchell, Burkov, and core systems literature.</p>
                </div>
              </div>
              <div className="feature-item">
                <div className="feature-icon-wrapper"><BrainCircuit size={18} /></div>
                <div className="feature-text">
                  <h4>Resume-Influenced Context</h4>
                  <p>Grills you dynamically on details listed in your profile, adapting difficulty based on performance.</p>
                </div>
              </div>
              <div className="feature-item">
                <div className="feature-icon-wrapper"><Award size={18} /></div>
                <div className="feature-text">
                  <h4>Structured Grading Metrics</h4>
                  <p>Provides detailed scores (0-10), technical critique, and competency analysis dashboards.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="glass-panel">
            <h3 style={{ marginBottom: '1.5rem', fontWeight: 700, fontSize: '1.25rem' }}>Start Screening Assessment</h3>
            <form onSubmit={startParsing}>
              <div className="form-group">
                <label className="form-label">Full Name</label>
                <div style={{ position: 'relative' }}>
                  <User style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} size={18} />
                  <input 
                    type="text" 
                    className="form-input" 
                    style={{ paddingLeft: '2.5rem' }} 
                    placeholder="Enter full name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Email Address</label>
                <div style={{ position: 'relative' }}>
                  <Mail style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} size={18} />
                  <input 
                    type="email" 
                    className="form-input" 
                    style={{ paddingLeft: '2.5rem' }} 
                    placeholder="Enter email address"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Target Interview Role</label>
                <div className="form-select-grid">
                  <div 
                    className={`role-card-option ${role === 'ai_ml' ? 'active' : ''}`}
                    onClick={() => setRole('ai_ml')}
                  >
                    <BrainCircuit size={20} color={role === 'ai_ml' ? '#6366f1' : '#64748b'} />
                    <span className="option-title">AI / ML</span>
                    <span className="option-desc">Tom Mitchell, Burkov</span>
                  </div>
                  
                  <div 
                    className={`role-card-option ${role === 'data_science' ? 'active' : ''}`}
                    onClick={() => setRole('data_science')}
                  >
                    <TrendingUp size={20} color={role === 'data_science' ? '#6366f1' : '#64748b'} />
                    <span className="option-title">Data Science</span>
                    <span className="option-desc">Müller, Brownlee</span>
                  </div>

                  <div 
                    className={`role-card-option ${role === 'backend' ? 'active' : ''}`}
                    onClick={() => setRole('backend')}
                  >
                    <Briefcase size={20} color={role === 'backend' ? '#6366f1' : '#64748b'} />
                    <span className="option-title">Backend</span>
                    <span className="option-desc">APIs, SQL, Systems</span>
                  </div>
                </div>
              </div>

              <div className="form-group" style={{ marginTop: '1.5rem' }}>
                <label className="form-label">Resume Upload (PDF / TXT)</label>
                <label className="dropzone">
                  <input 
                    type="file" 
                    accept=".pdf,.txt" 
                    style={{ display: 'none' }} 
                    onChange={handleFileChange}
                  />
                  <UploadCloud className="dropzone-icon" size={36} />
                  {file ? (
                    <div>
                      <p style={{ fontWeight: 600, color: '#f8fafc', fontSize: '0.9rem' }}>{file.name}</p>
                      <p style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.25rem' }}>Click or drag to replace</p>
                    </div>
                  ) : (
                    <div>
                      <p style={{ fontWeight: 600, fontSize: '0.9rem' }}>Choose a file or drag it here</p>
                      <p style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.25rem' }}>PDF or text files accepted up to 10MB</p>
                    </div>
                  )}
                </label>
              </div>

              <button 
                type="submit" 
                className="btn btn-primary" 
                style={{ width: '100%', marginTop: '1.5rem' }}
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <span className="loading-spinner"></span>
                    <span>Initializing Session...</span>
                  </>
                ) : (
                  <>
                    <span>Upload & Parse Profile</span>
                    <ChevronRight size={18} />
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* STEP 2: RESUME PARSING LOADING SCREEN */}
      {step === 'parsing' && (
        <div className="glass-panel text-center flex-center" style={{ flexDirection: 'column', padding: '4rem 2rem', minHeight: '350px' }}>
          <div className="loading-spinner" style={{ width: '48px', height: '48px', borderWidth: '4px', marginBottom: '2rem' }}></div>
          <h3 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }} className="pulse">Parsing Resume Profile</h3>
          <p style={{ color: '#94a3b8', maxWidth: '400px' }}>
            We are analyzing your resume structure, extracting technical skills, and compiling domain focus areas using GPT-4o-mini...
          </p>
        </div>
      )}

      {/* STEP 3: SKILLS EXTRACTION PREVIEW */}
      {step === 'extracted' && extractedSkills && (
        <div className="glass-panel" style={{ animation: 'fadeIn 0.4s ease-out' }}>
          <h3 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: '0.5rem' }}>Resume Profiling Complete</h3>
          <p style={{ color: '#94a3b8', marginBottom: '2rem' }}>
            Here is the profile summary we extracted. We will use these skills to ground the technical interview questions.
          </p>
          
          <div style={{
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid rgba(255, 255, 255, 0.05)',
            borderRadius: '12px',
            padding: '1.5rem',
            marginBottom: '2rem'
          }}>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.5rem' }}>Experience & Domain Exposure</h4>
            <p style={{ color: '#cbd5e1', fontSize: '0.95rem', lineHeight: '1.6' }}>{extractedSkills.experience_summary}</p>
          </div>

          <div className="skills-grid">
            <div>
              <h4 className="form-label" style={{ marginBottom: '0.5rem' }}>Identified Tech Stack & Tools</h4>
              <div className="chip-container">
                {extractedSkills.technologies && extractedSkills.technologies.map((t, idx) => (
                  <span key={idx} className="tech-chip">{t}</span>
                ))}
              </div>

              <h4 className="form-label" style={{ marginTop: '1.5rem', marginBottom: '0.5rem' }}>Core Technical Skills</h4>
              <div className="chip-container">
                {extractedSkills.skills && extractedSkills.skills.map((s, idx) => (
                  <span key={idx} className="skill-chip">{s}</span>
                ))}
              </div>
            </div>

            <div style={{ borderLeft: '1px solid rgba(255, 255, 255, 0.05)', paddingLeft: '2rem' }}>
              <h4 className="form-label" style={{ marginBottom: '0.75rem' }}>Evaluation Modules Selected</h4>
              <ul style={{ listStyleType: 'none', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {extractedSkills.suggested_topics && extractedSkills.suggested_topics.map((topic, idx) => (
                  <li key={idx} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', color: '#94a3b8' }}>
                    <CheckCircle2 size={16} color="#6366f1" />
                    <span>{topic}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '3rem' }}>
            <button className="btn btn-secondary" onClick={resetInterview}>Start Over</button>
            <button className="btn btn-primary" onClick={startInterview}>
              <span>Start Assessment (5 Questions)</span>
              <ArrowRight size={18} />
            </button>
          </div>
        </div>
      )}

      {/* STEP 4: INTERACTIVE INTERVIEW PANEL */}
      {step === 'interview' && (
        <div className="interview-layout">
          <div className="glass-panel question-card">
            <div className="question-header">
              <span className="question-number">Question {currentQuestion.number} of 5</span>
              <span style={{
                background: 'rgba(99, 102, 241, 0.15)',
                color: '#a5b4fc',
                fontSize: '0.75rem',
                fontWeight: 700,
                padding: '0.25rem 0.5rem',
                borderRadius: '4px',
                textTransform: 'uppercase'
              }}>Active Session</span>
            </div>

            <h3 className="question-text">{currentQuestion.text}</h3>

            <div className="form-group" style={{ marginTop: '1rem' }}>
              <label className="form-label">Your Technical Answer</label>
              <textarea 
                className="answer-textarea" 
                placeholder="Type your structured explanation here. Be detailed, mention core concepts, formulas, or system architectural patterns where appropriate..."
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
              />
              <div className="word-count-indicator">
                {answer.split(/\s+/).filter(Boolean).length} words
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1.5rem' }}>
              <button 
                className="btn btn-primary" 
                onClick={submitAnswer}
                disabled={isSubmitting || !answer.trim()}
              >
                {isSubmitting ? (
                  <>
                    <span className="loading-spinner"></span>
                    <span>Submitting to Evaluator...</span>
                  </>
                ) : (
                  <>
                    <span>Submit Answer</span>
                    <Send size={16} />
                  </>
                )}
              </button>
            </div>
          </div>

          {/* SIDEBAR TRACKER */}
          <div className="sidebar-panel">
            <div className="glass-panel" style={{ padding: '1.5rem' }}>
              <h4 className="sidebar-title">Interview Progression</h4>
              <div className="tracker-steps">
                {[1, 2, 3, 4, 5].map((num) => {
                  let stepClass = '';
                  let icon = num;
                  
                  if (currentQuestion.number === num) {
                    stepClass = 'active';
                  } else if (currentQuestion.number > num) {
                    stepClass = 'completed';
                    icon = <Check size={14} />;
                  }

                  return (
                    <div key={num} className={`tracker-step ${stepClass}`}>
                      <div className="step-circle">{icon}</div>
                      <span className="step-label">
                        {num === 1 && "Warm-up"}
                        {num === 2 && "Algorithm Deep-dive"}
                        {num === 3 && "Practical Application"}
                        {num === 4 && "Edge Cases / Optimization"}
                        {num === 5 && "Foundations & Theory"}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
            
            <div className="glass-panel" style={{ padding: '1.5rem', background: 'rgba(56, 189, 248, 0.02)', borderColor: 'rgba(56, 189, 248, 0.1)' }}>
              <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.5rem' }}>
                <HelpCircle size={16} />
                <span>Evaluation Note</span>
              </h4>
              <p style={{ fontSize: '0.8rem', color: '#94a3b8', lineHeight: '1.5' }}>
                Answers are matched against vector embeddings of core technical documents. Avoid generic statements; focus on technical depth, parameters, and algorithms.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* STEP 5: INTERMEDIATE GRADING AND FEEDBACK */}
      {step === 'grading' && lastGrading && (
        <div className="glass-panel" style={{ maxWidth: '800px', margin: '0 auto', animation: 'fadeIn 0.4s ease-out' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifySelf: 'start', gap: '1rem', marginBottom: '1.5rem' }}>
            <Award size={36} color="#6366f1" />
            <div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 800 }}>Answer Graded</h3>
              <p style={{ fontSize: '0.85rem', color: '#64748b' }}>Question {currentQuestion.number - (evaluationReport ? 0 : 1)} of 5</p>
            </div>
          </div>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '1.5rem',
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid rgba(255, 255, 255, 0.05)',
            borderRadius: '12px',
            padding: '1.5rem',
            marginBottom: '2rem'
          }}>
            {/* Circular Progress Bar */}
            <div style={{ position: 'relative', width: '70px', height: '70px' }}>
              <svg width="70" height="70" viewBox="0 0 36 36" style={{ transform: 'rotate(-90deg)' }}>
                <circle cx="18" cy="18" r="16" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="2.5"></circle>
                <circle 
                  cx="18" 
                  cy="18" 
                  r="16" 
                  fill="none" 
                  stroke={lastGrading.score >= 7 ? '#10b981' : lastGrading.score >= 5 ? '#f59e0b' : '#ef4444'} 
                  strokeWidth="2.5"
                  strokeDasharray={`${lastGrading.score * 10}, 100`}
                ></circle>
              </svg>
              <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', fontWeight: 800, fontSize: '1.1rem' }}>
                {lastGrading.score}
              </div>
            </div>
            <div>
              <h4 style={{ fontWeight: 700, fontSize: '1rem' }}>Technical Assessment Score</h4>
              <p style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Concept mapping: {lastGrading.traceability}</p>
            </div>
          </div>

          <div style={{ marginBottom: '2.5rem' }}>
            <h4 className="form-label" style={{ marginBottom: '0.5rem' }}>Critique & Suggestions</h4>
            <div style={{
              background: 'rgba(0, 0, 0, 0.2)',
              border: '1px solid rgba(255, 255, 255, 0.02)',
              borderRadius: '8px',
              padding: '1.25rem',
              color: '#cbd5e1',
              fontSize: '0.95rem',
              lineHeight: '1.6'
            }}>
              {lastGrading.feedback}
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button className="btn btn-primary" onClick={handleProceedFromGrading}>
              <span>{evaluationReport ? "View Final Results Dashboard" : "Proceed to Next Question"}</span>
              <ChevronRight size={18} />
            </button>
          </div>
        </div>
      )}

      {/* STEP 6: FINAL ANALYTICS REPORT */}
      {step === 'results' && evaluationReport && (
        <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
          <div className="glass-panel" style={{ marginBottom: '2rem' }}>
            <div className="results-header-summary">
              <div>
                <span className="question-number" style={{ color: '#38bdf8' }}>Hiring Assessment Verdict</span>
                <h2 style={{ fontSize: '2.2rem', fontWeight: 800, marginTop: '0.25rem', marginBottom: '0.5rem' }}>
                  {name}
                </h2>
                <p style={{ color: '#94a3b8' }}>
                  Target Role: <strong>{getRoleLabel(role)}</strong> &bull; Email: <strong>{email}</strong>
                </p>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                {/* SVG Circular score widget */}
                <div className="radial-container">
                  <svg width="90" height="90" viewBox="0 0 36 36" style={{ transform: 'rotate(-90deg)' }}>
                    <circle cx="18" cy="18" r="16" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="3"></circle>
                    <circle 
                      cx="18" 
                      cy="18" 
                      r="16" 
                      fill="none" 
                      stroke="url(#grad)" 
                      strokeWidth="3"
                      strokeDasharray={`${evaluationReport.overall_score}, 100`}
                    ></circle>
                    <defs>
                      <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#6366f1" />
                        <stop offset="100%" stopColor="#38bdf8" />
                      </linearGradient>
                    </defs>
                  </svg>
                  <div className="radial-text">{evaluationReport.overall_score}%</div>
                </div>

                <div>
                  <h4 style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: '#64748b', letterSpacing: '0.05em' }}>Overall Rating</h4>
                  <div className={`verdict-badge verdict-${evaluationReport.verdict ? evaluationReport.verdict.replace(/\s+/g, '-') : 'Recommend'} `} style={{ marginTop: '0.25rem' }}>
                    {evaluationReport.verdict || 'Recommend'}
                  </div>
                </div>
              </div>
            </div>

            {/* Final Summary Card */}
            <div style={{
              background: 'rgba(99, 102, 241, 0.05)',
              border: '1px solid rgba(99, 102, 241, 0.15)',
              borderRadius: '12px',
              padding: '1.5rem',
              marginBottom: '2rem'
            }}>
              <h4 style={{ fontWeight: 700, color: '#a5b4fc', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <BrainCircuit size={18} />
                <span>Executive Evaluation Summary</span>
              </h4>
              <p style={{ color: '#e2e8f0', fontSize: '0.95rem', lineHeight: '1.6' }}>
                {evaluationReport.summary}
              </p>
            </div>

            {/* Competency Ratings */}
            <div className="competencies-section">
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem', marginBottom: '1rem' }}>Technical Competencies Map</h3>
              <div className="competencies-grid">
                {evaluationReport.competencies && Object.entries(evaluationReport.competencies).map(([compName, scoreVal]) => (
                  <div key={compName} className="competency-card">
                    <span className="competency-title">{compName}</span>
                    <div className="competency-score-row">
                      <span className="competency-score-value">{scoreVal}%</span>
                    </div>
                    <div className="progress-bar-bg">
                      <div className="progress-bar-fill" style={{ width: `${scoreVal}%` }}></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Strengths and Weaknesses Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginTop: '2rem' }}>
              <div style={{ background: 'rgba(16, 185, 129, 0.02)', border: '1px solid rgba(16, 185, 129, 0.15)', borderRadius: '12px', padding: '1.5rem' }}>
                <h4 style={{ fontWeight: 700, color: '#34d399', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <CheckCircle2 size={18} />
                  <span>Demonstrated Strengths</span>
                </h4>
                <ul style={{ listStylePosition: 'inside', display: 'flex', flexDirection: 'column', gap: '0.5rem', color: '#cbd5e1', fontSize: '0.9rem' }}>
                  {evaluationReport.strengths && evaluationReport.strengths.map((str, idx) => (
                    <li key={idx} style={{ lineHeight: 1.5 }}>{str}</li>
                  ))}
                </ul>
              </div>

              <div style={{ background: 'rgba(239, 68, 68, 0.02)', border: '1px solid rgba(239, 68, 68, 0.15)', borderRadius: '12px', padding: '1.5rem' }}>
                <h4 style={{ fontWeight: 700, color: '#f87171', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <AlertTriangle size={18} />
                  <span>Recommended Improvements</span>
                </h4>
                <ul style={{ listStylePosition: 'inside', display: 'flex', flexDirection: 'column', gap: '0.5rem', color: '#cbd5e1', fontSize: '0.9rem' }}>
                  {evaluationReport.improvements && evaluationReport.improvements.map((imp, idx) => (
                    <li key={idx} style={{ lineHeight: 1.5 }}>{imp}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* Detailed Question breakdown */}
          <div className="glass-panel">
            <h3 style={{ fontSize: '1.25rem', fontWeight: 800, marginBottom: '0.5rem' }}>Detailed Interview Log</h3>
            <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: '1.5rem' }}>Review the chronological records of the interview questions, your answers, and the AI examiner's critiques.</p>

            <div className="qa-breakdown-list">
              {qaHistory.map((rec) => (
                <div key={rec.question_number} className="qa-card-review">
                  <div className="qa-card-header">
                    <span style={{ fontWeight: 700, fontSize: '0.9rem', color: '#6366f1' }}>
                      Question #{rec.question_number}
                    </span>
                    <span className="qa-score-indicator" style={{
                      borderColor: rec.evaluation_score >= 7 ? 'rgba(16, 185, 129, 0.3)' : rec.evaluation_score >= 5 ? 'rgba(245, 158, 11, 0.3)' : 'rgba(239, 68, 68, 0.3)',
                      color: rec.evaluation_score >= 7 ? '#34d399' : rec.evaluation_score >= 5 ? '#fbbf24' : '#f87171'
                    }}>
                      Score: {rec.evaluation_score}/10
                    </span>
                  </div>

                  <p style={{ fontWeight: 600, fontSize: '1.05rem', color: '#f8fafc', marginBottom: '1rem' }}>{rec.question_text}</p>
                  
                  <div className="review-label">Your Response</div>
                  <div className="review-content" style={{ whiteSpace: 'pre-wrap' }}>{rec.candidate_answer}</div>

                  <div className="review-label">Examiner Critique</div>
                  <div className="review-feedback-text" style={{
                    background: 'rgba(255, 255, 255, 0.01)',
                    padding: '0.75rem 1rem',
                    borderRadius: '8px',
                    border: '1px solid rgba(255, 255, 255, 0.02)',
                    marginTop: '0.5rem'
                  }}>{rec.evaluation_feedback}</div>
                </div>
              ))}
            </div>

            <div style={{ display: 'flex', justifyContent: 'center', marginTop: '3rem' }}>
              <button className="btn btn-primary" onClick={resetInterview}>
                <RefreshCw size={16} />
                <span>Start Another Session</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
