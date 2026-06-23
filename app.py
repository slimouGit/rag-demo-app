import os
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

from config import APP_DEBUG, UPLOAD_DIR
from database import (
    init_db,
    get_db_overview,
    get_chunks_for_document,
    delete_document,
    delete_chunk,
)
from ragservice import RagService
from ollamaservice import OllamaService


app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR

os.makedirs(UPLOAD_DIR, exist_ok=True)
init_db()

rag_service = RagService()
ollama_service = OllamaService()


@app.route("/", methods=["GET"])
def index():
    return render_page()


@app.route("/upload", methods=["POST"])
def upload():
    try:
        file = request.files.get("file")

        if not file or file.filename == "":
            raise ValueError("Bitte eine Datei auswählen.")

        filename = secure_filename(file.filename)

        if not filename.lower().endswith((".txt", ".pdf")):
            raise ValueError("Nur TXT- und PDF-Dateien werden unterstützt.")

        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        chunk_count = rag_service.ingest_document(filename, file_path)

        return render_page(
            message=f"Dokument wurde indexiert: {filename} ({chunk_count} Chunks)",
            selected_document=filename,
        )

    except Exception as e:
        return render_page(error=str(e))


@app.route("/ingest-url", methods=["POST"])
def ingest_url():
    try:
        url = request.form.get("url")

        if not url:
            raise ValueError("Bitte eine URL eingeben.")

        document_name, chunk_count = rag_service.ingest_url(url)

        return render_page(
            message=f"URL wurde indexiert: {document_name} ({chunk_count} Chunks)",
            selected_document=document_name,
        )

    except Exception as e:
        return render_page(error=str(e))


@app.route("/ask", methods=["POST"])
def ask():
    try:
        document_names = request.form.getlist("document_names")
        if not document_names:
            document_name = request.form.get("document_name")
            if document_name:
                document_names = [document_name]
        question = request.form.get("question")

        if not document_names:
            raise ValueError("Bitte mindestens ein Dokument auswählen.")

        if not question:
            raise ValueError("Bitte eine Frage eingeben.")

        result = rag_service.ask(document_names, question)

        return render_page(
            selected_document=document_names[0],
            selected_documents=document_names,
            question=question,
            answer=result["answer"],
            chunks=result["chunks"],
        )

    except Exception as e:
        return render_page(error=str(e))


@app.route("/set-chat-model", methods=["POST"])
def set_chat_model():
    model = request.form.get("chat_model")
    if model:
        try:
            rag_service.set_chat_model(model)
        except ValueError as e:
            return render_page(error=str(e))
    return render_page(message=f"Chat-Modell gesetzt: {model}")


@app.route("/set-embedding-model", methods=["POST"])
def set_embedding_model():
    model = request.form.get("embedding_model")
    if model:
        try:
            rag_service.set_embedding_model(model)
        except ValueError as e:
            return render_page(error=str(e))
    return render_page(message=f"Embedding-Modell gesetzt: {model}")


@app.route("/db", methods=["GET"])
def db_view():
    selected_document = request.args.get("document_name")

    overview = get_db_overview()
    db_chunks = []

    if selected_document:
        db_chunks = get_chunks_for_document(selected_document)

    return render_page(
        db_overview=overview,
        db_chunks=db_chunks,
        db_selected_document=selected_document,
    )


@app.route("/db/delete-document", methods=["POST"])
def db_delete_document():
    document_name = request.form.get("document_name")

    if document_name:
        delete_document(document_name)

    overview = get_db_overview()

    return render_page(
        message="Dokument wurde aus der Datenbank gelöscht.",
        db_overview=overview,
        db_chunks=[],
        db_selected_document=None,
    )


@app.route("/db/delete-chunk", methods=["POST"])
def db_delete_chunk():
    chunk_id = request.form.get("chunk_id")
    document_name = request.form.get("document_name")

    if chunk_id:
        delete_chunk(int(chunk_id))

    overview = get_db_overview()
    db_chunks = get_chunks_for_document(document_name) if document_name else []

    return render_page(
        message="Chunk wurde gelöscht.",
        db_overview=overview,
        db_chunks=db_chunks,
        db_selected_document=document_name,
    )


def render_page(
    message=None,
    error=None,
    selected_document=None,
    selected_documents=None,
    question=None,
    answer=None,
    chunks=None,
    db_overview=None,
    db_chunks=None,
    db_selected_document=None,
):
    documents = rag_service.get_documents()

    chat_models = []
    embedding_models = []
    model_error = None

    try:
        all_models = ollama_service.list_models()
        embedding_terms = ("embed", "embedding", "bge", "minilm")
        embedding_models = [
            m for m in all_models if any(t in m.lower() for t in embedding_terms)
        ]
        chat_models = [
            m for m in all_models if not any(t in m.lower() for t in embedding_terms)
        ]
    except Exception as e:
        model_error = str(e)

    chat_model = rag_service.current_chat_model
    embedding_model = rag_service.current_embedding_model

    return render_template(
        "index.html",
        documents=documents,
        chat_models=chat_models,
        embedding_models=embedding_models,
        chat_model=chat_model,
        embedding_model=embedding_model,
        model_error=model_error,
        message=message,
        error=error,
        selected_document=selected_document,
        selected_documents=selected_documents or [],
        question=question,
        answer=answer,
        chunks=chunks or [],
        db_overview=db_overview,
        db_chunks=db_chunks or [],
        db_selected_document=db_selected_document,
    )


if __name__ == "__main__":
    app.run(debug=APP_DEBUG)
