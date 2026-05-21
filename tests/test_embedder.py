import pytest

from pman.embedder import Chunk, TextEmbedder


class TestChunkText:
    def test_empty_text_returns_empty_list(self):
        embedder = TextEmbedder()
        assert embedder.chunk_text("") == []

    def test_single_chunk(self):
        embedder = TextEmbedder(chunk_size=10)
        chunks = embedder.chunk_text("one two three four five six seven eight nine ten")
        assert len(chunks) == 1
        assert chunks[0].text == "one two three four five six seven eight nine ten"

    def test_multiple_chunks(self):
        embedder = TextEmbedder(chunk_size=5, chunk_overlap=0)
        text = " ".join(str(i) for i in range(20))
        chunks = embedder.chunk_text(text)
        assert len(chunks) == 4
        assert len(chunks[0].text.split()) == 5

    def test_chunk_overlap(self):
        embedder = TextEmbedder(chunk_size=10, chunk_overlap=5)
        text = " ".join(str(i) for i in range(30))
        chunks = embedder.chunk_text(text)
        assert len(chunks) == 6
        assert len(chunks[0].text.split()) == 10

    def test_chunk_metadata(self):
        embedder = TextEmbedder(chunk_size=10)
        chunks = embedder.chunk_text("some text here", chapter_number=5, topic="wbs")
        assert len(chunks) == 1
        assert chunks[0].chapter_number == 5
        assert chunks[0].topic == "wbs"


class TestEmbedChunks:
    def test_empty_list_returns_empty(self):
        embedder = TextEmbedder()
        result = embedder.embed_chunks([])
        assert result == []

    def test_unknown_provider_raises(self):
        embedder = TextEmbedder()
        with pytest.raises(ValueError, match="Unknown provider"):
            embedder.embed_chunks([Chunk(text="test")], provider="unknown")
