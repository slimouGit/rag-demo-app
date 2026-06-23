import requests
from config import OLLAMA_BASE_URL


class OllamaService:
    def __init__(self):
        """Store the configured base URL for Ollama API calls."""
        self.base_url = OLLAMA_BASE_URL

    def get_models(self) -> list[dict]:
        """Fetch raw model metadata from Ollama."""
        response = requests.get(f"{self.base_url}/api/tags", timeout=10)
        response.raise_for_status()
        return response.json().get("models", [])

    def detect_embedding_model(self) -> str:
        """Pick the first available model that looks like an embedding model."""
        models = self.get_models()

        for model in models:
            name = model.get("name", "").lower()
            if (
                "embed" in name
                or "embedding" in name
                or "bge" in name
                or "minilm" in name
            ):
                return model["name"]

        raise RuntimeError(
            "Kein Embedding-Modell gefunden. "
            "Bitte z. B. ausführen: ollama pull nomic-embed-text"
        )

    def detect_chat_model(self) -> str:
        """Pick the first available model that looks like a chat model."""
        models = self.get_models()

        chat_models = []
        for model in models:
            name = model.get("name", "").lower()
            if not any(
                term in name for term in ["embed", "embedding", "bge", "minilm"]
            ):
                chat_models.append(model)

        if not chat_models:
            raise RuntimeError(
                "Kein Chat-Modell gefunden. "
                "Bitte z. B. ausführen: ollama pull llama3.2"
            )

        return chat_models[0]["name"]

    def list_models(self) -> list[str]:
        """Return only model names from the Ollama model list."""
        return [m.get("name", "") for m in self.get_models()]

    def embed(self, text: str, model: str = None) -> list[float]:
        """Create an embedding vector for the given text."""
        if model is None:
            model = self.detect_embedding_model()

        payload = {"model": model, "input": text}

        response = requests.post(
            f"{self.base_url}/api/embed", json=payload, timeout=120
        )
        response.raise_for_status()

        data = response.json()
        embeddings = data.get("embeddings")

        if not embeddings:
            raise RuntimeError("Ollama hat keine Embeddings geliefert.")

        return embeddings[0]

    def generate_answer(self, context: str, question: str, model: str = None) -> str:
        """Generate a grounded answer from context and question."""
        if model is None:
            model = self.detect_chat_model()

        prompt = f"""
Du bist ein RAG-Assistent.

Beantworte die Frage ausschließlich auf Basis des bereitgestellten Kontexts.
Wenn die Antwort nicht im Kontext steht, sage:
"Diese Information steht nicht im Dokument."

KONTEXT:
{context}

FRAGE:
{question}

ANTWORT:
"""

        payload = {"model": model, "prompt": prompt, "stream": False}

        response = requests.post(
            f"{self.base_url}/api/generate", json=payload, timeout=180
        )
        response.raise_for_status()

        return response.json().get("response", "").strip()
