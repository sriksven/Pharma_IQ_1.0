import sys
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.config import settings
from app.routes import schema as schema_router
from app.routes import chat as chat_router
from app.routes import sessions as sessions_router
from app.routes import metrics as metrics_router
from app.routes import data as data_router


app = FastAPI(title="Pharma_IQ_1.0 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(schema_router.router, prefix="/api/v1")
app.include_router(chat_router.router, prefix="/api/v1")
app.include_router(sessions_router.router, prefix="/api/v1")
app.include_router(metrics_router.router, prefix="/api/v1")
app.include_router(data_router.router, prefix="/api/v1")


@app.on_event("startup")
async def startup():
    from data_pipeline.ingest import load_all_tables
    from data_pipeline.registry import build_registry
    from chat_pipeline.db import init_db

    await init_db()
    tables = load_all_tables(settings.data_dir)
    build_registry(tables, settings.data_dir)


@app.get("/health")
def health():
    return {"status": "ok"}
