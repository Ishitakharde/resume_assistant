"""
resume_parser.py
-----------------
Extracts plain text from an uploaded resume file.
Supports .pdf (via pypdf) and .txt directly.
"""

from pypdf import PdfReader
import io


def extract_text(file_storage) -> str:
    """
    file_storage: a Flask FileStorage object (from request.files['resume'])
    Returns extracted plain text.
    """
    filename = (file_storage.filename or "").lower()

    if filename.endswith(".pdf"):
        return _extract_pdf(file_storage)
    elif filename.endswith(".txt"):
        return file_storage.read().decode("utf-8", errors="ignore")
    else:
        raise ValueError("Unsupported file type. Please upload a .pdf or .txt resume.")


def _extract_pdf(file_storage) -> str:
    data = file_storage.read()
    reader = PdfReader(io.BytesIO(data))
    text_parts = []
    for page in reader.pages:
        text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts).strip()
