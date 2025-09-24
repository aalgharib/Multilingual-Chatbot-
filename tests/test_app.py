import sys
import json
from pathlib import Path

import pytest
from chalice.test import Client

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app


@pytest.fixture
def client():
    return Client(app)


def test_chat_endpoint_returns_response_and_session(client):
    response = client.http.post(
        "/chat",
        headers={"Content-Type": "application/json"},
        body=json.dumps(
            {
                "message": "Hello",
                "source_language": "en",
                "target_language": "es",
                "session_id": "test-session",
            }
        ),
    )
    assert response.status_code == 200
    body = response.json_body
    assert body["session_id"] == "test-session"
    assert body["source_language"] == "en"
    assert body["target_language"] == "es"
    assert isinstance(body["response"], str)
    assert "Hello" in body["response"]


def test_chat_history_endpoint_reflects_previous_messages(client):
    client.http.post(
        "/chat",
        headers={"Content-Type": "application/json"},
        body=json.dumps(
            {
                "message": "Testing history",
                "source_language": "en",
                "target_language": "en",
                "session_id": "history-session",
            }
        ),
    )

    response = client.http.get("/chat-history/history-session")
    assert response.status_code == 200
    history = response.json_body
    assert len(history) == 1
    record = history[0]
    assert record["user_input"] == "Testing history"
    assert "Testing history" in record["bot_response"]


def test_reset_history_endpoint(client):
    client.http.post(
        "/chat",
        headers={"Content-Type": "application/json"},
        body=json.dumps({"message": "Reset me", "session_id": "reset-session"}),
    )
    response = client.http.delete("/chat-history/reset-session")
    assert response.status_code == 200
    body = response.json_body
    assert body == {"session_id": "reset-session", "cleared": True}

    history_response = client.http.get("/chat-history/reset-session")
    assert history_response.status_code == 200
    assert history_response.json_body == []


def test_text_to_speech_returns_audio_payload(client):
    response = client.http.post(
        "/text-to-speech",
        headers={"Content-Type": "application/json", "Accept": "audio/mpeg"},
        body=json.dumps({"text": "Hello world", "language_code": "en-US", "voice_id": "Joanna"}),
    )
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "audio/mpeg"
    assert response.body.startswith(b"ID3")


def test_empty_chat_message_returns_default_prompt(client):
    response = client.http.post(
        "/chat",
        headers={"Content-Type": "application/json"},
        body=json.dumps({"session_id": "empty-session", "message": ""}),
    )
    assert response.status_code == 200
    assert response.json_body["response"] == "I'm ready whenever you want to chat."
