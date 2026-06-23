from io import BytesIO

from fastapi import HTTPException
from pypdf import PdfReader


def extract_pdf_text(content: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Could not read that PDF file.") from exc

    text = "\n".join(page.strip() for page in pages if page.strip()).strip()
    if not text:
        raise HTTPException(status_code=400, detail="No readable text was found in that PDF.")
    return text


def extract_text_file(content: bytes) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Only UTF-8 text files are supported.") from exc
