import pytest
from chalice.test import Client
from app import app


@pytest.fixture
def client():
    return Client(app)


def test_chat_endpoint(client):
    response = client.http.post(
        "/chat",
        json={
            "message": "Hello",
            "source_language": "en",
            "target_language": "es",
            "session_id": "test-session",
        },
    )
    assert response.status_code == 200
    body = response.json_body
    assert "response" in body
    assert "source_language" in body
    assert "target_language" in body


def test_text_to_speech_endpoint(client):
    response = client.http.post(
        "/text-to-speech",
        json={"text": "Hello world", "language_code": "en-US", "voice_id": "Joanna"},
    )
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "audio/mpeg"


def test_chat_history_endpoint(client):
    response = client.http.get("/chat-history/test-session")
    assert response.status_code == 200
    assert isinstance(response.json_body, list)


def test_invalid_chat_request(client):
    response = client.http.post("/chat", json={})
    assert response.status_code == 200  # Should handle empty message gracefully
    body = response.json_body
    assert "response" in body
