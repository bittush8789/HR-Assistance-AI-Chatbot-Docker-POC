import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from app.config import settings
from app.rag import RAGPipelineError, rag_pipeline

# Configure application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("hr_assistant.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    logger.info("Initializing HR Assistance AI Chatbot service...")
    if not settings.is_api_key_set:
        logger.warning(
            "⚠️ OPENAI_API_KEY is not configured or is a placeholder. "
            "Chat and indexing endpoints will return degraded status until a valid key is provided."
        )
    else:
        logger.info(f"OpenAI configuration: model={settings.openai_model}, embedding={settings.openai_embedding_model}")
        try:
            indexed_count = rag_pipeline.get_indexed_count()
            logger.info(f"ChromaDB persistent collection '{settings.chroma_collection_name}' currently has {indexed_count} indexed chunks.")
        except Exception as exc:
            logger.warning(f"Could not check ChromaDB on startup: {exc}")

    yield
    logger.info("Shutting down HR Assistance AI Chatbot service.")


app = FastAPI(
    title="HR Assistance AI Chatbot POC",
    description=(
        "Proof of Concept (POC) for an HR Assistance AI Chatbot powered by FastAPI, "
        "LangChain, OpenAI GPT-4o mini, and persistent ChromaDB vector storage."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# -----------------------------------------------------------------------------
# Request & Response Schemas
# -----------------------------------------------------------------------------

class ChatRequest(BaseModel):
    """Schema for employee question submission."""

    question: str = Field(
        ...,
        description="The HR question to ask the chatbot.",
        examples=["What is the annual leave policy?"],
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Question cannot be empty or whitespace only.")
        return trimmed


class ChatResponse(BaseModel):
    """Schema for chatbot response with ground-truth sources."""

    question: str
    answer: str
    sources: List[str]


class IndexRequest(BaseModel):
    """Schema for manual indexing control."""

    force: bool = Field(
        default=False,
        description="Force rebuild of ChromaDB collection even if already populated.",
    )


class IndexResponse(BaseModel):
    """Schema for document indexing status response."""

    status: str
    message: str
    details: Dict[str, Any]


class HealthResponse(BaseModel):
    """Schema for application health check response."""

    status: str
    openai_configured: bool
    model: str
    embedding_model: str
    vector_store: str
    indexed_chunks: int


# -----------------------------------------------------------------------------
# Custom Exception Handlers
# -----------------------------------------------------------------------------

@app.exception_handler(RAGPipelineError)
async def handle_rag_error(request: Request, exc: RAGPipelineError):
    """Handle domain errors from the RAG pipeline with clean HTTP status codes."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    """Handle input validation errors with human-readable error descriptions."""
    first_error = exc.errors()[0] if exc.errors() else {}
    msg = first_error.get("msg", "Invalid request payload.")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": f"Validation error: {msg}"},
    )


@app.exception_handler(Exception)
async def handle_generic_exception(request: Request, exc: Exception):
    """Fallback handler to prevent exposing internal stack traces or secrets."""
    logger.error(f"Unhandled server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact the administrator."},
    )


# -----------------------------------------------------------------------------
# API Endpoints
# -----------------------------------------------------------------------------

@app.get("/", summary="Root Welcome")
async def root():
    """Service information and link to Swagger documentation."""
    return {
        "service": "HR Assistance AI Chatbot POC",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_url": "/health",
        "chat_url": "/chat",
        "index_url": "/index",
    }


@app.get("/health", response_model=HealthResponse, summary="Application Health Check")
async def health():
    """
    Return application health status, configuration readiness,
    and current count of indexed chunks in ChromaDB.
    """
    is_configured = settings.is_api_key_set
    indexed_chunks = 0
    vector_status = "unavailable"

    if is_configured:
        try:
            indexed_chunks = rag_pipeline.get_indexed_count()
            vector_status = "ready"
        except Exception:
            vector_status = "error"
    else:
        vector_status = "missing_api_key"

    overall_status = "healthy" if (is_configured and vector_status == "ready") else "degraded"

    return HealthResponse(
        status=overall_status,
        openai_configured=is_configured,
        model=settings.openai_model,
        embedding_model=settings.openai_embedding_model,
        vector_store=vector_status,
        indexed_chunks=indexed_chunks,
    )


@app.post("/chat", response_model=ChatResponse, summary="Submit Question to HR Chatbot")
async def chat(request: ChatRequest):
    """
    Process employee question against indexed HR policy documents.
    Retrieves grounded context and generates an answer using OpenAI GPT-4o mini.
    """
    result = rag_pipeline.answer_question(request.question)
    return ChatResponse(
        question=result["question"],
        answer=result["answer"],
        sources=result["sources"],
    )


@app.post("/index", response_model=IndexResponse, summary="Initialize or Rebuild Document Index")
async def index_documents(request: Optional[IndexRequest] = None):
    """
    Load HR documents from data/documents/, generate embeddings, and store in ChromaDB.
    Avoids duplicate indexing unless force=true is passed.
    """
    force = request.force if request else False
    result = rag_pipeline.index_documents(force=force)

    return IndexResponse(
        status=result["status"],
        message=result["message"],
        details=result,
    )
