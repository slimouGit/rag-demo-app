# Local RAG Demo App

A local demo project that shows the core workflow of Retrieval-Augmented Generation (RAG) with Flask/FastAPI, SQLite, and Ollama.

This repository is intentionally built as a learning and portfolio project. It is simple, transparent, and easy to run locally. It is **not** a production-ready RAG system.

## What This Project Demonstrates

- Local document ingestion from TXT, PDF, and public URLs
- Text chunking with overlap
- Embedding generation with local Ollama models
- Storage of chunks and embeddings in SQLite
- Semantic retrieval with cosine similarity and top-k selection
- Answer generation grounded in retrieved context
- A simple Flask UI and a lightweight FastAPI interface

## Tech Stack

- Python 3.11+
- Flask (web UI)
- FastAPI + Uvicorn (API)
- SQLite (storage)
- Ollama (local embeddings + local generation)
- pypdf, requests
- pytest, black

## Architecture Overview

The app follows a small, explicit RAG pipeline:

1. Load a document (file or URL).
2. Extract text.
3. Split text into chunks.
4. Generate embeddings per chunk.
5. Store chunks + embeddings in SQLite.
6. Generate query embedding.
7. Compute cosine similarity against stored chunks.
8. Select top-k chunks.
9. Generate final answer from selected context.

Core modules:

- `documentservice.py`: text extraction and defensive URL ingestion
- `ragservice.py`: chunking, retrieval, ranking, generation flow
- `ollamaservice.py`: communication with Ollama API
- `database.py`: SQLite schema and data access helpers
- `app.py`: Flask UI routes
- `api.py`: FastAPI endpoints for demo workflow

## Project Structure

```text
rag-demo-app/
+-- app.py
+-- api.py
+-- config.py
+-- database.py
+-- documentservice.py
+-- ollamaservice.py
+-- ragservice.py
+-- requirements.txt
+-- README.md
+-- .gitignore
+-- templates/
¦   +-- index.html
+-- uploads/
¦   +-- .gitkeep
+-- examples/
¦   +-- company_policy.txt
+-- tests/
    +-- test_chunking.py
    +-- test_similarity.py
    +-- test_documentservice.py
```

## Requirements

- Python 3.11+
- Ollama installed and running locally
- At least one chat model and one embedding model available in Ollama

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Ollama Setup

Example model setup:

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

Check local Ollama availability:

```bash
curl http://localhost:11434/api/tags
```

## Start Flask Web UI

```bash
python app.py
```

Open:

- `http://127.0.0.1:5000`

## Start FastAPI API

```bash
uvicorn api:app --reload --port 8000
```

Open:

- `http://127.0.0.1:8000/docs`

## Typical Workflow

1. Start Ollama.
2. Start Flask UI or FastAPI.
3. Select chat/embedding models.
4. Ingest document or URL.
5. Ask a question.
6. Review retrieved chunks and scores.

## API Endpoints (Demo Scope)

- `GET /api/health`
- `GET /api/ollama/status`
- `POST /api/ollama/chat-model`
- `POST /api/ollama/embedding-model`
- `GET /api/documents`
- `POST /api/documents/url`
- `POST /api/ask`
- `DELETE /api/documents/{document_name}`

Note: File upload via FastAPI is intentionally not implemented in this demo and is tracked as a future TODO.

## Example Document and Question

Sample file:

- `examples/company_policy.txt`

Example question:

- `How often must employees complete security awareness training?`

Expected example answer:

- `Employees must complete security awareness training once per quarter.`

## Screenshots

Add screenshots here after running locally:

- `[Placeholder] Flask home with model selection`
- `[Placeholder] Ingestion success message`
- `[Placeholder] Answer with retrieved chunks and scores`
- `[Placeholder] FastAPI Swagger UI`

## Limitations

- Demo-oriented architecture with simple linear retrieval in Python
- No authentication or authorization
- No multi-user isolation
- Embeddings stored as JSON text in SQLite for readability, not scale
- Basic error handling and no background processing

## Security and Demo Notes

- This project is for local learning and demo usage only.
- Do not deploy it as-is to production.
- Flask debug mode should be enabled only for local development.
- URL ingestion blocks local/private network targets and keeps request timeout and response size limits.

## Future Improvements

- Add FastAPI file upload endpoint
- Add async job queue for larger ingests
- Add metadata filters and better retrieval controls
- Add containerized setup (Docker)
- Add CI for lint/test automation
