from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from typing import List
from pathlib import Path
import os
import asyncio
import io
import json
import pdfplumber

from .ai_extractor import extract_data
from .file_service import create_output_file
from .config import OUTPUT_DIR

app = FastAPI(title="AI Data Entry Agent")

def extract_text_from_bytes(content: bytes, filename: str) -> str:
    if filename.lower().endswith(".pdf"):
        text = ""
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
        return text.strip()
    return content.decode(errors="ignore")

# ───────────────────────────────
# PATH SETUP
# ───────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

# Serve static files (CSS + JS)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# ───────────────────────────────
# FRONTEND ROUTE
# ───────────────────────────────

@app.get("/")
def serve_frontend():
    return FileResponse(FRONTEND_DIR / "index.html")

# ───────────────────────────────
# OPTIONAL: HEALTH CHECK
# ───────────────────────────────

@app.get("/health")
def health():
    return {"status": "AI Data Entry Agent running"}

# ───────────────────────────────
# CONCURRENCY CONTROL
# ───────────────────────────────

# Limit concurrent OpenAI calls (prevents rate-limit crashes)
semaphore = asyncio.Semaphore(5)

async def limited_extract(text: str, prompt: str):
    async with semaphore:
        return await asyncio.to_thread(extract_data, text, prompt)

# ───────────────────────────────
# PROCESS FILES
# ───────────────────────────────

@app.post("/process")
async def process_files(
    files: List[UploadFile] = File(...),
    prompt: str = Form(...),
    output_format: str = Form("csv")
):
    tasks = []

    # Read files and prepare async tasks
    for file in files:
        content = await file.read()
        text = extract_text_from_bytes(content, file.filename)
        tasks.append(limited_extract(text, prompt))

    # Run AI calls concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_results = []

    for result in results:
        if isinstance(result, Exception):
            print("File processing error:", result)
            continue

        if result:
            if isinstance(result, dict):
                all_results.append(result)
            elif isinstance(result, list):
                all_results.extend(result)

    if not all_results:
        return {"error": "No data extracted."}

    filename, path = create_output_file(all_results, output_format)

    return {
        "download_url": f"/download/{filename}"
    }

# ───────────────────────────────
# DOWNLOAD FILE
# ───────────────────────────────

@app.get("/download/{filename}")
def download_file(filename: str):
    file_path = os.path.join(OUTPUT_DIR, filename)

    if not os.path.exists(file_path):
        return {"error": "File not found"}

    return FileResponse(file_path, filename=filename)

# ───────────────────────────────
# EXTRACT SINGLE FILE → JSON
# ───────────────────────────────

@app.post("/extract")
async def extract_single(
    file: UploadFile = File(...),
    prompt: str = Form(...)
):
    content = await file.read()
    text = extract_text_from_bytes(content, file.filename)
    result = await limited_extract(text, prompt)

    if result is None:
        return {"error": "Extraction failed", "filename": file.filename}

    return {"filename": file.filename, "data": result}

# ───────────────────────────────
# BUILD OUTPUT FROM EXTRACTED JSON
# ───────────────────────────────

@app.post("/build_output")
async def build_output(
    data: str = Form(...),
    output_format: str = Form("csv")
):
    try:
        parsed = json.loads(data)
    except Exception:
        return {"error": "Invalid JSON data"}

    if isinstance(parsed, dict):
        all_data = [parsed]
    elif isinstance(parsed, list):
        all_data = parsed
    else:
        return {"error": "Unexpected data shape"}

    filename, _ = create_output_file(all_data, output_format)
    if not filename:
        return {"error": "Could not create output file"}

    return {"download_url": f"/download/{filename}"}