import json
import base64
from PyPDF2 import PdfReader
from PIL import Image
import pytesseract
from io import BytesIO

def extract_text_from_pdf(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def extract_text_from_image(data: bytes) -> str:
    img = Image.open(BytesIO(data))
    return pytesseract.image_to_string(img)

def extract_text_from_plain(data: bytes) -> str:
    return data.decode("utf-8", errors="ignore")

def run(task: dict, context: dict) -> dict:
    files = context.get("files", {})
    extracted = {}

    for name, b64 in files.items():
        raw = base64.b64decode(b64)

        if name.lower().endswith(".pdf"):
            extracted[name] = extract_text_from_pdf(raw)
        elif name.lower().endswith((".png", ".jpg", ".jpeg")):
            extracted[name] = extract_text_from_image(raw)
        else:
            extracted[name] = extract_text_from_plain(raw)

    return {
        "status": "ok",
        "extracted": extracted
    }
