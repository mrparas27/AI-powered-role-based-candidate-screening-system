import io
import json
import PyPDF2
from openai import OpenAI
from backend.app.config import OPENAI_API_KEY

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extracts text from PDF file bytes."""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return ""

def parse_resume_content(resume_text: str) -> dict:
    """Uses LLM to parse extracted resume text into structured fields."""
    if not resume_text or not resume_text.strip():
        return {
            "skills": ["Software Engineering"],
            "technologies": ["Python"],
            "domain_exposure": ["Full-Stack Development"],
            "experience_summary": "No resume text provided.",
            "suggested_topics": ["Coding Practices", "Software Design", "Debugging"]
        }

    if not OPENAI_API_KEY:
        # Fallback if key is missing
        return {
            "skills": ["Software Engineering (Fallback)"],
            "technologies": ["Python (Fallback)"],
            "domain_exposure": ["Systems Engineering"],
            "experience_summary": "Extracted with fallback. Please set OPENAI_API_KEY.",
            "suggested_topics": ["Data Structures", "Algorithms", "APIs"]
        }

    client = OpenAI(api_key=OPENAI_API_KEY)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are a senior technical recruiter. Extract structured information from the candidate's resume "
                        "and output a JSON object with the following fields:\n"
                        "- skills (list of strings): Core engineering skills (e.g. 'Machine Learning', 'API Design')\n"
                        "- technologies (list of strings): Programming languages, frameworks, databases, or cloud tools (e.g. 'Python', 'React', 'Docker')\n"
                        "- domain_exposure (list of strings): Industries or functional domains (e.g. 'E-commerce', 'Computer Vision')\n"
                        "- experience_summary (string): Short 1-2 sentence overview of the candidate's background\n"
                        "- suggested_topics (list of strings): 3-5 technical topics derived from their background that would be suitable for technical assessment."
                    )
                },
                {"role": "user", "content": f"Parse the following resume:\n\n{resume_text}"}
            ],
            temperature=0.2
        )
        data = json.loads(response.choices[0].message.content)
        return data
    except Exception as e:
        print(f"Error in LLM resume parser: {e}")
        return {
            "skills": ["Software Development"],
            "technologies": ["Python", "Git"],
            "domain_exposure": ["Backend Engineering"],
            "experience_summary": "Failed to parse resume text with OpenAI. Using fallback extract.",
            "suggested_topics": ["Core Engineering", "Problem Solving", "System Fundamentals"]
        }
