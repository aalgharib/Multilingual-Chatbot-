import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app


@pytest.fixture
def client():
    app.config.update({"TESTING": True})
    with app.test_client() as test_client:
        yield test_client


def test_chat_endpoint_returns_response_and_session(client):
    response = client.post(
        "/chat",
        json={
            "message": "Hello",
            "source_language": "en",
            "target_language": "es",
            "session_id": "test-session",
        },
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["session_id"] == "test-session"
    assert body["source_language"] == "en"
    assert body["target_language"] == "es"
    assert isinstance(body["response"], str)
    assert "Hello" in body["response"]


def test_chat_history_endpoint_reflects_previous_messages(client):
    client.post(
        "/chat",
        json={
            "message": "Testing history",
            "source_language": "en",
            "target_language": "en",
            "session_id": "history-session",
        },
    )

    response = client.get("/chat-history/history-session")
    assert response.status_code == 200
    history = response.get_json()
    assert len(history) == 1
    record = history[0]
    assert record["user_input"] == "Testing history"
    assert "Testing history" in record["bot_response"]


def test_reset_history_endpoint(client):
    client.post(
        "/chat",
        json={"message": "Reset me", "session_id": "reset-session"},
    )
    response = client.delete("/chat-history/reset-session")
    assert response.status_code == 200
    body = response.get_json()
    assert body == {"session_id": "reset-session", "cleared": True}

    history_response = client.get("/chat-history/reset-session")
    assert history_response.status_code == 200
    assert history_response.get_json() == []


def test_text_to_speech_returns_audio_payload(client):
    response = client.post(
        "/text-to-speech",
        json={"text": "Hello world", "language_code": "en-US", "voice_id": "Joanna"},
    )
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "audio/mpeg"
    assert response.data.startswith(b"ID3")


def test_empty_chat_message_returns_default_prompt(client):
    response = client.post(
        "/chat",
        json={"session_id": "empty-session", "message": ""},
    )
    assert response.status_code == 200
    assert response.get_json()["response"] == "I'm ready whenever you want to chat."
