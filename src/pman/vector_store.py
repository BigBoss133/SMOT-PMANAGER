import hashlib
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from pman.config import settings
from pman.embedder import Chunk, TextEmbedder
from pman.pdf_extractor import PDFExtractor


_SECTION_TO_TOPIC = {
    "charter": "charter",
    "raci": "stakeholder/raci",
    "stakeholder": "stakeholder/raci",
    "wbs": "wbs",
    "schedule": "wbs",
    "risks": "risks",
    "risk": "risks",
    "budget": "budget",
    "agile": "agile",
}


class VectorStore:
    def __init__(
        self,
        chroma_path: str | None = None,
        collection_name: str | None = None,
    ):
        self.chroma_path = chroma_path or settings.rag_chroma_path
        self.collection_name = collection_name or settings.rag_chroma_collection
        self._client: Optional[chromadb.ClientAPI] = None
        self._collection: Optional[chromadb.Collection] = None

    def _get_client(self) -> chromadb.ClientAPI:
        if self._client is None:
            Path(self.chroma_path).mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=self.chroma_path,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return self._client

    def _get_collection(self) -> chromadb.Collection:
        if self._collection is None:
            self._collection = self._get_client().get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def is_initialized(self) -> bool:
        try:
            coll = self._get_collection()
            return coll.count() > 0
        except Exception:
            return False

    def add_documents(
        self,
        chunks: list[Chunk],
        embeddings: list[list[float]],
    ) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have same length")
        if not chunks:
            return

        collection = self._get_collection()
        ids = []
        documents = []
        metadatas = []
        embs = []

        for chunk, embedding in zip(chunks, embeddings):
            chunk_id = hashlib.md5(chunk.text.encode()).hexdigest()
            ids.append(chunk_id)
            documents.append(chunk.text)
            metadatas.append({
                "chapter_number": chunk.chapter_number,
                "topic": chunk.topic,
            })
            embs.append(embedding)

        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embs,
            metadatas=metadatas,
        )

    def search(
        self,
        query_embedding: list[float],
        k: int = 5,
        filter_metadata: Optional[dict] = None,
    ) -> list[dict]:
        collection = self._get_collection()
        where = None
        if filter_metadata:
            where = {key: {"$eq": value} for key, value in filter_metadata.items()}

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=where,
        )

        output = []
        if results and results["documents"]:
            for idx in range(len(results["documents"][0])):
                output.append({
                    "text": results["documents"][0][idx],
                    "metadata": results["metadatas"][0][idx] if results["metadatas"] else {},
                    "distance": results["distances"][0][idx] if results["distances"] else 0.0,
                })
        return output

    def search_by_section(
        self,
        section_name: str,
        query_embedding: list[float],
        k: int = 5,
    ) -> list[dict]:
        topic = _SECTION_TO_TOPIC.get(section_name.lower(), "general")
        return self.search(query_embedding, k=k, filter_metadata={"topic": topic})

    def initialize_from_pdf(self, pdf_path: str | None = None) -> None:
        pdf_path = pdf_path or settings.rag_pdf_path
        extractor = PDFExtractor(pdf_path)
        chapters = extractor.extract_chapters()

        if not chapters:
            raise ValueError(f"No chapters found in PDF: {pdf_path}")

        embedder = TextEmbedder(
            chunk_size=settings.rag_chunk_size,
            chunk_overlap=settings.rag_chunk_overlap,
        )

        all_chunks: list[Chunk] = []
        for chapter in chapters:
            chunks = embedder.chunk_text(
                chapter.text,
                chapter_number=chapter.number,
                topic=chapter.topic,
            )
            all_chunks.extend(chunks)

        if not all_chunks:
            raise ValueError("No chunks generated from PDF")

        embeddings = embedder.embed_chunks(all_chunks, provider="ollama")

        self.add_documents(all_chunks, embeddings)
