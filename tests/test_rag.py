from unittest.mock import patch

from pman.rag import RAGContext, RAGPipeline


class TestRAGPipeline:
    @patch("pman.embedder.TextEmbedder.embed_chunks")
    def test_query_with_empty_store(self, mock_embed):
        mock_embed.return_value = [[0.1] * 768]
        rag = RAGPipeline()
        result = rag.query("What is WBS?")
        assert isinstance(result, RAGContext)
        assert result.question == "What is WBS?"

    @patch("pman.embedder.TextEmbedder.embed_chunks")
    def test_query_section(self, mock_embed):
        mock_embed.return_value = [[0.1] * 768]
        rag = RAGPipeline()
        result = rag.query_section("wbs", "What is WBS?")
        assert result.section_filter == "wbs"

    def test_cache_hit(self):
        rag = RAGPipeline()
        key = rag._get_cache_key("test", None)
        rag._set_cached(key, [{"text": "cached"}])
        cached = rag._get_cached(key)
        assert cached is not None
        assert cached[0]["text"] == "cached"

    def test_cache_expires(self):
        rag = RAGPipeline()
        key = rag._get_cache_key("test", None)
        rag._set_cached(key, [{"text": "old"}])
        rag._cache_ttl = 0
        cached = rag._get_cached(key)
        assert cached is None
