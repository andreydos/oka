from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.chat.chat_controller import router as chat_router
from app.config import settings
from app.db.session import engine, init_db
from app.dependencies import get_llm_client, get_vector_repository
from app.documents.document_controller import router as documents_router
from app.ml_mutex import is_ml_busy
from app.schemas import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    vector_repo = get_vector_repository()
    await vector_repo.ensure_collection()
    yield


app = FastAPI(title="Offline Knowledge Assistant", version="0.1.0", lifespan=lifespan)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)
app.include_router(chat_router)


@app.get("/api/v1/health", response_model=HealthResponse)
async def health():
    db_status = "ok"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    vector_repo = get_vector_repository()
    qdrant_status = "ok" if await vector_repo.is_available() else "error"

    llm = get_llm_client()
    ollama_status = "ok" if await llm.is_available() else "error"

    overall = "ok" if all(s == "ok" for s in [db_status, qdrant_status, ollama_status]) else "degraded"

    return HealthResponse(
        status=overall,
        database=db_status,
        qdrant=qdrant_status,
        ollama=ollama_status,
        ollama_busy=is_ml_busy(),
    )
