"""
GET /api/v1/data/csv/{filename}   -- Download a raw CSV
GET /api/v1/data/json/{filename}  -- Return CSV rows as JSON for in-UI preview
"""

import os
import csv
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

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

