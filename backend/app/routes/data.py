"""
GET /api/v1/data/csv/{filename}   -- Download a raw CSV
GET /api/v1/data/json/{filename}  -- Return CSV rows as JSON for in-UI preview
"""

import os
import csv
import shutil
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from data_pipeline.ingest import load_all_tables
from data_pipeline.registry import build_registry

router = APIRouter()

DATA_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "data_pipeline", "raw"
)


def _resolve(filename: str) -> str:
    """Resolve and validate the file path, raising 400/404 as appropriate."""
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")
    if not filename.endswith(".csv"):
        filename = filename + ".csv"
    file_path = os.path.abspath(os.path.join(DATA_DIR, filename))
    if not file_path.startswith(os.path.abspath(DATA_DIR)):
        raise HTTPException(status_code=400, detail="Invalid path.")
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found.")
    return file_path, filename


@router.get("/data/csv/{filename}")
def download_csv(filename: str):
    """Return the CSV file as a download attachment."""
    file_path, filename = _resolve(filename)
    return FileResponse(
        path=file_path,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/data/json/{filename}")
def preview_csv(filename: str):
    """Return CSV rows as a JSON list of dicts for in-UI preview."""
    file_path, filename = _resolve(filename)
    rows = []
    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    columns = list(rows[0].keys()) if rows else []
    return {"filename": filename, "columns": columns, "rows": rows}


@router.post("/data/upload")
async def upload_csv(file: UploadFile = File(...)):
    """Upload a new CSV file and dynamically re-register all data sources."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are allowed.")
    
    file_path = os.path.join(DATA_DIR, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Re-trigger the ingestion pipeline
        tables = load_all_tables(DATA_DIR)
        build_registry(tables, DATA_DIR)
        
        return {"status": "success", "filename": file.filename, "tables_loaded": len(tables)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
