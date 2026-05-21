"""Fixtures condivise per i test di SMOT-PMANAGER."""

from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pman.api import app
from pman.models import Base


@pytest.fixture()
def db_session():
    """Sessione SQLAlchemy su SQLite in-memory con tabelle create."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture()
def client():
    """FastAPI TestClient."""
    from starlette.testclient import TestClient

    return TestClient(app)


@pytest.fixture()
def mock_ollama():
    """Mock di OllamaClient.generate."""
    with patch(
        "pman.ollama.OllamaClient.generate",
        return_value={"response": "test"},
    ) as mocked:
        yield mocked
