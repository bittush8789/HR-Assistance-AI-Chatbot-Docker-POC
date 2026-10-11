import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.rag import HRRAGPipeline, INSUFFICIENT_INFO_MESSAGE


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint returns discovery metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "HR Assistance AI Chatbot POC"
    assert "/docs" in data["docs_url"]


def test_health_endpoint_degraded_when_no_api_key(client, monkeypatch):
    """Test /health endpoint indicates missing credentials gracefully."""
    monkeypatch.setattr(settings, "openai_api_key", "")
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["openai_configured"] is False
    assert data["vector_store"] == "missing_api_key"


def test_health_endpoint_healthy_with_valid_key(client, monkeypatch):
    """Test /health endpoint indicates healthy when configured."""
    monkeypatch.setattr(settings, "openai_api_key", "sk-mock-valid-key-for-testing")
    with patch.object(HRRAGPipeline, "get_indexed_count", return_value=12):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["openai_configured"] is True
        assert data["indexed_chunks"] == 12
        assert data["vector_store"] == "ready"


def test_chat_validation_empty_or_whitespace_question(client):
    """Test validation rejection for empty or whitespace-only questions."""
    # Empty string
    response = client.post("/chat", json={"question": ""})
    assert response.status_code == 400
    assert "detail" in response.json()

    # Whitespace only
    response = client.post("/chat", json={"question": "   \n\t  "})
    assert response.status_code == 400
    assert "detail" in response.json()


def test_chat_missing_api_key(client, monkeypatch):
    """Test /chat returns 503 when OpenAI API key is missing."""
    monkeypatch.setattr(settings, "openai_api_key", "")
    response = client.post("/chat", json={"question": "What is the leave policy?"})
    assert response.status_code == 503
    assert "OpenAI API key is missing" in response.json()["detail"]


def test_chat_relevant_question_success(client, monkeypatch):
    """Test successful chat interaction with mocked RAG pipeline."""
    monkeypatch.setattr(settings, "openai_api_key", "sk-mock-valid-key")
    mock_rag_response = {
        "question": "What is the annual leave policy?",
        "answer": "Full-time employees accrue 20 paid annual leave days per calendar year.",
        "sources": ["leave_policy.txt"],
    }
    with patch("app.main.rag_pipeline.answer_question", return_value=mock_rag_response):
        response = client.post(
            "/chat",
            json={"question": "What is the annual leave policy?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["question"] == "What is the annual leave policy?"
        assert "20 paid annual leave days" in data["answer"]
        assert data["sources"] == ["leave_policy.txt"]


def test_chat_unrelated_question_fallback(client, monkeypatch):
    """Test query on unrelated topic returns fallback response with empty sources."""
    monkeypatch.setattr(settings, "openai_api_key", "sk-mock-valid-key")
    mock_rag_response = {
        "question": "What is the recipe for chocolate cake?",
        "answer": INSUFFICIENT_INFO_MESSAGE,
        "sources": [],
    }
    with patch("app.main.rag_pipeline.answer_question", return_value=mock_rag_response):
        response = client.post(
            "/chat",
            json={"question": "What is the recipe for chocolate cake?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "do not contain sufficient information" in data["answer"]
        assert data["sources"] == []


def test_documents_load_correctly():
    """Verify that predefined HR documents exist and load with expected filenames."""
    pipeline = HRRAGPipeline()
    docs = pipeline.load_hr_documents()
    assert len(docs) == 4

    filenames = {doc.metadata["source"] for doc in docs}
    expected = {
        "leave_policy.txt",
        "work_from_home.txt",
        "expense_policy.txt",
        "employee_benefits.txt",
    }
    assert filenames == expected
    for doc in docs:
        assert len(doc.page_content) > 100
