from dataclasses import dataclass
from pathlib import Path


@dataclass
class Chunk:
    text: str
    chapter_number: int = 0
    topic: str = "general"


class TextEmbedder:
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str, chapter_number: int = 0, topic: str = "general") -> list[Chunk]:
        if not text:
            return []
        words = text.split()
        if len(words) <= self.chunk_size:
            return [Chunk(text=" ".join(words), chapter_number=chapter_number, topic=topic)]
        chunks = []
        step = max(1, self.chunk_size - self.chunk_overlap)
        for i in range(0, len(words), step):
            chunk_words = words[i:i + self.chunk_size]
            if not chunk_words:
                break
            chunk_text = " ".join(chunk_words)
            if chunk_text:
                chunks.append(Chunk(
                    text=chunk_text,
                    chapter_number=chapter_number,
                    topic=topic,
                ))
        return chunks

    def embed_chunks(self, chunks: list[Chunk], provider: str = "ollama", model: str | None = None) -> list[list[float]]:
        from pman.config import settings

        if not chunks:
            return []

        if provider == "ollama":
            return self._embed_ollama(chunks, model or settings.embedding_model)
        elif provider == "openai":
            return self._embed_openai(chunks, model or settings.embedding_model)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def _embed_ollama(self, chunks: list[Chunk], model: str) -> list[list[float]]:
        import json
        import urllib.request
        from pman.config import settings

        host = settings.ollama_host.rstrip("/")
        embeddings = []
        for chunk in chunks:
            data = {
                "model": model,
                "prompt": chunk.text,
            }
            payload = json.dumps(data).encode("utf-8")
            req = urllib.request.Request(
                f"{host}/api/embeddings",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode())
                embeddings.append(result["embedding"])
        return embeddings

    def _embed_openai(self, chunks: list[Chunk], model: str) -> list[list[float]]:
        import json
        import urllib.request
        from pman.config import settings

        api_key = settings.ai_openai_api_key
        if not api_key:
            raise ValueError("OpenAI API key not configured")

        texts = [chunk.text for chunk in chunks]
        data = {
            "model": model,
            "input": texts,
        }
        payload = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            "https://api.openai.com/v1/embeddings",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode())
            return [item["embedding"] for item in result["data"]]
