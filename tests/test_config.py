"""Test per pman.config — Settings e proprietà calcolate."""

import os
from unittest.mock import patch

from pman.config import Settings


class TestSettingsDefaults:
    """Valori di default senza env override."""

    def test_default_values(self):
        s = Settings()
        assert s.ollama_host == "http://10.0.0.2:11434"
        assert s.ollama_model == "gemma4-dev"
        assert s.db_path == "/tmp/pman.db"
        assert s.github_api_url == "https://api.github.com"

    def test_sqlalchemy_database_uri_default(self):
        s = Settings()
        assert s.sqlalchemy_database_uri == f"sqlite+aiosqlite:///{s.db_path}"

    def test_sqlalchemy_database_uri_override(self):
        s = Settings(DATABASE_URL="postgresql+asyncpg://user:pw@localhost/db")
        assert s.sqlalchemy_database_uri == "postgresql+asyncpg://user:pw@localhost/db"

    def test_effective_celery_broker_fallback(self):
        s = Settings()
        assert s.effective_celery_broker == s.redis_url

    def test_effective_celery_broker_explicit(self):
        s = Settings(CELERY_BROKER_URL="amqp://guest@localhost//")
        assert s.effective_celery_broker == "amqp://guest@localhost//"

    def test_effective_celery_backend_fallback(self):
        s = Settings()
        assert s.effective_celery_backend == s.redis_url


class TestSettingsEnvOverride:
    """Override tramite variabili d'ambiente."""

    def test_env_override_ollama_host(self):
        with patch.dict(os.environ, {"PMAN_OLLAMA_HOST": "http://custom:9999"}):
            s = Settings()
            assert s.ollama_host == "http://custom:9999"

    def test_env_override_ollama_model(self):
        with patch.dict(os.environ, {"PMAN_OLLAMA_MODEL": "llama3"}):
            s = Settings()
            assert s.ollama_model == "llama3"

    def test_env_override_db_path(self):
        with patch.dict(os.environ, {"PMAN_DB_PATH": "/data/test.db"}):
            s = Settings()
            assert s.db_path == "/data/test.db"
            assert "/data/test.db" in s.sqlalchemy_database_uri


class TestRAGSettings:
    def test_rag_defaults(self):
        s = Settings()
        assert s.rag_chunk_size == 512
        assert s.rag_chunk_overlap == 50
        assert s.rag_chroma_collection == "pm_textbook"
        assert s.rag_top_k == 5
        assert "chromadb" in s.rag_chroma_path

    def test_env_override_rag_chunk_size(self):
        with patch.dict(os.environ, {"PMAN_RAG_CHUNK_SIZE": "256"}):
            s = Settings()
            assert s.rag_chunk_size == 256


class TestAIProviderSettings:
    def test_ai_provider_defaults(self):
        s = Settings()
        assert s.ai_provider == "ollama"
        assert s.ai_ollama_model == "gemma4-dev"
        assert s.ai_openai_model == "gpt-4o-mini"
        assert s.ai_max_tokens == 2048
        assert s.ai_temperature == 0.3

    def test_embedding_model_ollama(self):
        s = Settings()
        assert s.embedding_model == "nomic-embed-text"

    def test_embedding_model_openai(self):
        with patch.dict(os.environ, {"PMAN_AI_PROVIDER": "openai"}):
            s = Settings()
            assert s.embedding_model == "text-embedding-3-small"


class TestProjectSettings:
    def test_projects_dir_default(self):
        s = Settings()
        assert ".pman" in s.projects_dir
        assert "projects" in s.projects_dir
