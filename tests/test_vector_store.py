import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from pman.vector_store import VectorStore


class TestIsInitialized:
    def test_empty_store_returns_false(self):
        tmp = tempfile.mkdtemp()
        store = VectorStore(chroma_path=tmp, collection_name="test_empty")
        assert store.is_initialized() is False


class TestAddDocuments:
    def test_add_and_search(self):
        tmp = tempfile.mkdtemp()
        store = VectorStore(chroma_path=tmp, collection_name="test_add")

        chunks = [
            type("Chunk", (), {"text": "WBS definition", "chapter_number": 13, "topic": "wbs"})(),
            type("Chunk", (), {"text": "Budget planning", "chapter_number": 17, "topic": "budget"})(),
        ]
        embeddings = [[0.1] * 768, [0.2] * 768]

        store.add_documents(chunks, embeddings)
        assert store.is_initialized() is True

    def test_empty_list_does_nothing(self):
        tmp = tempfile.mkdtemp()
        store = VectorStore(chroma_path=tmp, collection_name="test_empty_add")
        store.add_documents([], [])
        assert store.is_initialized() is False

    def test_mismatched_lengths_raises(self):
        tmp = tempfile.mkdtemp()
        store = VectorStore(chroma_path=tmp, collection_name="test_mismatch")
        with pytest.raises(ValueError, match="same length"):
            store.add_documents([type("C", (), {"text": "x", "chapter_number": 1, "topic": "wbs"})()], [[0.1] * 768, [0.2] * 768])


class TestSearch:
    def test_search_with_filter(self):
        tmp = tempfile.mkdtemp()
        store = VectorStore(chroma_path=tmp, collection_name="test_filter")

        chunks = [
            type("Chunk", (), {"text": "WBS breakdown", "chapter_number": 13, "topic": "wbs"})(),
            type("Chunk", (), {"text": "Risk management", "chapter_number": 18, "topic": "risks"})(),
        ]
        embeddings = [[0.1] * 768, [0.9] * 768]
        store.add_documents(chunks, embeddings)

        results = store.search([0.1] * 768, k=1, filter_metadata={"topic": "wbs"})
        assert len(results) == 1
        assert results[0]["metadata"]["topic"] == "wbs"

    def test_search_without_filter(self):
        tmp = tempfile.mkdtemp()
        store = VectorStore(chroma_path=tmp, collection_name="test_nofilter")

        chunks = [
            type("Chunk", (), {"text": "A", "chapter_number": 1, "topic": "general"})(),
            type("Chunk", (), {"text": "B", "chapter_number": 2, "topic": "general"})(),
        ]
        embeddings = [[0.1] * 768, [0.2] * 768]
        store.add_documents(chunks, embeddings)

        results = store.search([0.1] * 768, k=2)
        assert len(results) == 2


class TestSearchBySection:
    def test_section_to_topic_mapping(self):
        from pman.vector_store import _SECTION_TO_TOPIC
        assert _SECTION_TO_TOPIC["wbs"] == "wbs"
        assert _SECTION_TO_TOPIC["risks"] == "risks"
        assert _SECTION_TO_TOPIC["budget"] == "budget"
