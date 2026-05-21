import time
from dataclasses import dataclass, field
from typing import Optional

from pman.config import settings
from pman.embedder import TextEmbedder
from pman.vector_store import VectorStore


@dataclass
class RAGContext:
    question: str
    chunks: list[dict] = field(default_factory=list)
    section_filter: Optional[str] = None


class RAGPipeline:
    def __init__(self, vector_store: VectorStore | None = None):
        self.vector_store = vector_store or VectorStore()
        self.embedder = TextEmbedder()
        self._cache: dict[str, tuple[list[dict], float]] = {}
        self._cache_ttl = 300

    def _get_cache_key(self, question: str, section_filter: Optional[str]) -> str:
        return f"{section_filter or 'all'}:{question}"

    def _get_cached(self, key: str) -> Optional[list[dict]]:
        if key not in self._cache:
            return None
        results, timestamp = self._cache[key]
        if time.time() - timestamp > self._cache_ttl:
            del self._cache[key]
            return None
        return results

    def _set_cached(self, key: str, results: list[dict]) -> None:
        self._cache[key] = (results, time.time())

    def query(self, question: str, k: int = 5, section_filter: Optional[str] = None) -> RAGContext:
        cache_key = self._get_cache_key(question, section_filter)
        cached = self._get_cached(cache_key)
        if cached is not None:
            return RAGContext(question=question, chunks=cached, section_filter=section_filter)

        query_embedding = self.embedder.embed_chunks(
            [type("C", (), {"text": question})()],
            provider=settings.ai_provider,
        )[0]

        if section_filter:
            results = self.vector_store.search_by_section(
                section_filter, query_embedding, k=k
            )
        else:
            results = self.vector_store.search(query_embedding, k=k)

        self._set_cached(cache_key, results)
        return RAGContext(question=question, chunks=results, section_filter=section_filter)

    def query_section(self, section_name: str, question: str, k: int = 5) -> RAGContext:
        return self.query(question, k=k, section_filter=section_name)
