"""
llm_client.py
--------------
Thin wrapper around the Gemini REST API (via google-generativeai SDK).

Two things worth calling out for your resume/interview story:
  1. This is a REST API integration, same pattern as the Gemini call in
     DocuShield - prompt in, structured/plain text out.
  2. If no GEMINI_API_KEY is set, the client falls back to a simple
     rule-based responder so the app is still demoable without a paid key.
"""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import google.generativeai as genai
    _SDK_AVAILABLE = True
except ImportError:
    _SDK_AVAILABLE = False

API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
_configured = False

if _SDK_AVAILABLE and API_KEY:
    genai.configure(api_key=API_KEY)
    _configured = True


SYSTEM_INSTRUCTION = """You are Resume Assistant, an expert technical career coach.
You help engineering candidates:
  - Answer questions about their own resume (skills, projects, experience)
  - Compare their resume against a target job description
  - Suggest specific, honest wording changes - never invent skills or
    experience the candidate doesn't have
Keep answers concise and concrete. When tailoring, point to the exact
resume line and the exact JD requirement it addresses.
"""


def ask(resume_text: str, job_description: str, question: str, history: list) -> str:
    """
    resume_text: full parsed resume text
    job_description: optional JD text (may be empty)
    question: the user's current message
    history: list of {"role": "user"/"assistant", "content": str}
    """
    if _configured:
        return _ask_gemini(resume_text, job_description, question, history)
    return _ask_fallback(resume_text, job_description, question)


def _ask_gemini(resume_text, job_description, question, history) -> str:
    model = genai.GenerativeModel(
        model_name="gemini-3.6-flash",
        system_instruction=SYSTEM_INSTRUCTION,
    )

    context = f"RESUME:\n{resume_text}\n\n"
    if job_description:
        context += f"TARGET JOB DESCRIPTION:\n{job_description}\n\n"

    # Rebuild a short chat history so follow-up questions have context
    convo = model.start_chat(history=[
        {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]}
        for m in history
    ])

    prompt = context + f"QUESTION: {question}"
    response = convo.send_message(prompt)
    return response.text


def _ask_fallback(resume_text, job_description, question) -> str:
    """
    Minimal offline fallback so the app still runs end-to-end without an
    API key - useful for local demos/screen recordings for interviews.
    """
    q = question.lower()

    if "skill" in q and "match" in q or "fit" in q:
        return (
            "[Offline demo mode - set GEMINI_API_KEY for real answers]\n"
            "I'd normally compare your resume's skills section against the "
            "job description's requirements and list matches and gaps here."
        )
    if "tailor" in q or "rewrite" in q:
        return (
            "[Offline demo mode] I'd normally suggest specific line edits to "
            "your summary and bullet points so they mirror the JD's keywords, "
            "without adding anything not already on your resume."
        )
    return (
        "[Offline demo mode - no GEMINI_API_KEY set] "
        "Add a Gemini API key to get real, context-aware answers about your "
        f"resume. You asked: \"{question}\""
    )
