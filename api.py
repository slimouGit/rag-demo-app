from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database import delete_document
from ragservice import RagService

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

rag = RagService()


class ModelSelection(BaseModel):
    """Model payload used to set chat or embedding model names."""

    model: str


class UrlIngestRequest(BaseModel):
    """Payload for URL indexing requests."""

    url: str


class AskRequest(BaseModel):
    """Payload for RAG question answering requests."""

    document_names: list[str] = Field(default_factory=list)
    question: str


@app.get("/api/health")
def health() -> dict:
    """Return a simple service health indicator."""
    return {"ok": True, "service": "local-rag-demo-api"}


@app.get("/api/ollama/status")
def ollama_status() -> dict:
    """Return available local models and currently selected defaults."""
    try:
        return rag.get_ollama_status()
    except Exception as exc:
        raise HTTPException(
            status_code=503, detail=f"Ollama unavailable: {exc}"
        ) from exc


@app.post("/api/ollama/chat-model")
def set_chat_model(sel: ModelSelection) -> dict:
    """Set the chat/generation model if it is available."""
    try:
        rag.set_chat_model(sel.model)
        return {"ok": True, "current_chat_model": rag.current_chat_model}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=503, detail=f"Could not set chat model: {exc}"
        ) from exc


@app.post("/api/ollama/embedding-model")
def set_embedding_model(sel: ModelSelection) -> dict:
    """Set the embedding model if it is available."""
    try:
        rag.set_embedding_model(sel.model)
        return {"ok": True, "current_embedding_model": rag.current_embedding_model}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Could not set embedding model: {exc}",
        ) from exc


@app.get("/api/documents")
def list_documents() -> dict:
    """Return all indexed document names."""
    return {"documents": rag.get_documents()}


@app.post("/api/documents/url")
def ingest_document_url(payload: UrlIngestRequest) -> dict:
    """Index a public URL and store resulting chunks in SQLite."""
    try:
        document_name, chunk_count = rag.ingest_url(payload.url)
        return {
            "ok": True,
            "document_name": document_name,
            "chunk_count": chunk_count,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"URL ingest failed: {exc}"
        ) from exc


@app.post("/api/ask")
def ask(payload: AskRequest) -> dict:
    """Answer a question using selected indexed documents."""
    document_names = [name for name in payload.document_names if name.strip()]
    if not document_names:
        raise HTTPException(
            status_code=400, detail="Please provide at least one document name."
        )

    if not payload.question.strip():
        raise HTTPException(
            status_code=400, detail="Please provide a non-empty question."
        )

    try:
        result = rag.ask(document_names, payload.question)
        return {
            "ok": True,
            "question": payload.question,
            "documents": document_names,
            "answer": result["answer"],
            "chunks": result["chunks"],
            "used_models": result["used_models"],
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Question answering failed: {exc}"
        ) from exc


@app.delete("/api/documents/{document_name:path}")
def remove_document(document_name: str) -> dict:
    """Delete all chunks for the specified document name."""
    normalized = document_name.strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="Document name must not be empty.")

    delete_document(normalized)
    return {"ok": True, "deleted_document": normalized}


@app.get("/api/ollama/used")
def used_models() -> dict:
    """Return currently configured chat and embedding models."""
    return {
        "chat_model": rag.current_chat_model,
        "embedding_model": rag.current_embedding_model,
    }
