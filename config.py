import os

from dotenv import load_dotenv


load_dotenv()


def _get_int(name: str, default: int) -> int:
    """Read an integer environment variable with a safe fallback."""
    value = os.getenv(name)
    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(BASE_DIR, "uploads"))
DB_PATH = os.getenv("DB_PATH", os.path.join(BASE_DIR, "rag.db"))

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

CHUNK_SIZE = _get_int("CHUNK_SIZE", 1200)
CHUNK_OVERLAP = _get_int("CHUNK_OVERLAP", 200)
TOP_K = _get_int("TOP_K", 4)

WEB_REQUEST_TIMEOUT_SECONDS = _get_int("WEB_REQUEST_TIMEOUT_SECONDS", 10)
WEB_MAX_CONTENT_BYTES = _get_int("WEB_MAX_CONTENT_BYTES", 2_000_000)
WEB_USER_AGENT = os.getenv("WEB_USER_AGENT", "rag-demo-bot/1.0 (+local-dev)")

APP_DEBUG = os.getenv("APP_DEBUG", "0") == "1"
