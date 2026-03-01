from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from typing import List
from pathlib import Path
import os

from .ai_extractor import extract_data
from .file_service import create_output_file
from .config import OUTPUT_DIR

app = FastAPI(title="AI Data Entry Agent")

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
# PROCESS FILES
# ───────────────────────────────

@app.post("/process")
async def process_files(
    files: List[UploadFile] = File(...),
    prompt: str = Form(...),
    output_format: str = Form("csv")
):
    all_results = []

    for file in files:
        content = await file.read()
        text = content.decode(errors="ignore")

        result = await extract_data(text, prompt)

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