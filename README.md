# Resume Assistant

A chatbot that answers questions about your resume and tailors it against a
target job description — built with Python, Flask, a REST API integration
(Gemini), and SQLite.

## What it does

1. Upload a resume (PDF or TXT).
2. Optionally paste a target job description.
3. Chat with it:
   - "What skills am I missing for this JD?"
   - "Rewrite my professional summary to match this role."
   - "Which of my projects is most relevant and why?"

Conversation history is stored per-session in SQLite, so follow-up questions
have context from earlier in the chat.

## Architecture

```
Browser (HTML/CSS/JS chat UI)
      |  fetch() -> REST endpoints
      v
Flask app (app.py)
      |
      +--> utils/resume_parser.py   PDF/TXT -> plain text (pypdf)
      +--> utils/llm_client.py      Gemini REST API call (google-generativeai SDK)
      +--> database.py              SQLite: sessions + chat history
```

REST endpoints:
| Method | Route                    | Purpose                          |
|--------|--------------------------|-----------------------------------|
| POST   | `/api/upload`             | Upload resume + optional JD, get session_id |
| POST   | `/api/job-description`    | Update the JD for an existing session |
| POST   | `/api/chat`               | Ask a question, get a reply       |
| GET    | `/api/history/<session_id>` | Fetch past messages for a session |

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env        # then add your GEMINI_API_KEY
python app.py
```

Open http://127.0.0.1:5000

**No API key?** The app still runs — `utils/llm_client.py` falls back to a
simple offline responder so you can demo the full upload → chat → history
flow without needing a paid key.

## Why these choices (useful for your resume / interview talking points)

- **Python + Flask REST API** — same integration pattern as the Gemini call
  in DocuShield: structured prompt in, model response out, exposed over
  HTTP endpoints.
- **SQLite** — lightweight, file-based SQL database; lets the chatbot keep
  conversation memory per session without needing a server process.
- **Graceful degradation** — the LLM client checks for an API key and falls
  back to a rule-based responder rather than crashing, so the app is
  demoable in any environment.
- **Clear separation of concerns** — parsing, LLM calls, and storage are each
  isolated in their own module, so any one piece (e.g. swapping Gemini for
  another model) can change without touching the rest.

## Possible extensions

- Support .docx resumes (via `python-docx`)
- Multi-resume comparison against one JD
- Export the tailored suggestions as a diff against the original resume
