"""
app.py
------
Resume Assistant - a small Flask REST API + chat UI that:
  1. Accepts a resume upload (PDF/TXT)
  2. Optionally accepts a target job description
  3. Lets the user chat with an LLM (Gemini) about their resume -
     e.g. "What's missing for this JD?", "Rewrite my summary for this role"

Architecture:
  Browser (templates/index.html + static/script.js)
        |  fetch() calls
        v
  Flask REST API (this file)
        |
        +--> utils/resume_parser.py   (PDF -> text)
        +--> utils/llm_client.py      (Gemini REST API call)
        +--> database.py              (SQLite: sessions + chat history)

Run:
    pip install -r requirements.txt
    export GEMINI_API_KEY=your_key_here   # optional, falls back to demo mode
    python app.py
Then open http://127.0.0.1:5000
"""

from flask import Flask, request, jsonify, render_template
import database
from utils import resume_parser, llm_client

app = Flask(__name__)
database.init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/upload", methods=["POST"])
def upload_resume():
    """
    Multipart form fields:
      - resume: file (.pdf or .txt)          [required]
      - job_description: string              [optional]
    Returns: { session_id, resume_preview }
    """
    if "resume" not in request.files:
        return jsonify({"error": "No resume file uploaded"}), 400

    file = request.files["resume"]
    job_description = request.form.get("job_description", "")

    try:
        resume_text = resume_parser.extract_text(file)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    if not resume_text.strip():
        return jsonify({"error": "Could not extract any text from that file"}), 400

    session_id = database.create_session(resume_text, job_description)

    return jsonify({
        "session_id": session_id,
        "resume_preview": resume_text[:400] + ("..." if len(resume_text) > 400 else ""),
    })


@app.route("/api/job-description", methods=["POST"])
def set_job_description():
    """Update or add a target JD to an existing session."""
    data = request.get_json(force=True)
    session_id = data.get("session_id")
    job_description = data.get("job_description", "")

    if not database.get_session(session_id):
        return jsonify({"error": "Unknown session_id"}), 404

    database.update_job_description(session_id, job_description)
    return jsonify({"ok": True})


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    JSON body: { session_id, message }
    Returns: { reply }
    """
    data = request.get_json(force=True)
    session_id = data.get("session_id")
    message = (data.get("message") or "").strip()

    session = database.get_session(session_id)
    if not session:
        return jsonify({"error": "Unknown session_id - upload a resume first"}), 404
    if not message:
        return jsonify({"error": "Empty message"}), 400

    history = database.get_history(session_id)

    reply = llm_client.ask(
        resume_text=session["resume_text"],
        job_description=session["job_description"] or "",
        question=message,
        history=history,
    )

    database.add_message(session_id, "user", message)
    database.add_message(session_id, "assistant", reply)

    return jsonify({"reply": reply})


@app.route("/api/history/<int:session_id>", methods=["GET"])
def history(session_id):
    if not database.get_session(session_id):
        return jsonify({"error": "Unknown session_id"}), 404
    return jsonify({"history": database.get_history(session_id)})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
