"""Flask API entrypoint for the multilingual chatbot."""
from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Dict, List

from flask import Flask, Response as FlaskResponse, jsonify, make_response, request, send_from_directory
from flask_cors import CORS

from ml.orchestrator import PromptOrchestrator

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    supports_credentials=False,
    max_age=600,
)


class ChatHistoryRepository:
    """In-memory storage for chat history records keyed by session."""

    def __init__(self) -> None:
        self._store: Dict[str, List[Dict[str, str]]] = {}

    def append(
        self,
        session_id: str,
        user_input: str,
        bot_response: str,
        source_language: str,
        target_language: str,
    ) -> None:
        record = {
            "session_id": session_id,
            "user_input": user_input,
            "bot_response": bot_response,
            "source_language": source_language,
            "target_language": target_language,
        }
        self._store.setdefault(session_id, []).append(record)

    def get(self, session_id: str) -> List[Dict[str, str]]:
        return list(self._store.get(session_id, []))

    def clear(self, session_id: str) -> None:
        self._store.pop(session_id, None)


class OrchestratorPool:
    """Maintain a LangChain orchestrator per session to preserve memory."""

    def __init__(self, model_path: str | None, generation_config: Dict[str, object] | None) -> None:
        self._model_path = model_path
        self._generation_config = generation_config
        self._instances: Dict[str, PromptOrchestrator] = {}

    def get(self, session_id: str) -> PromptOrchestrator:
        if session_id not in self._instances:
            self._instances[session_id] = PromptOrchestrator(
                model_path=self._model_path, generation_config=self._generation_config
            )
        return self._instances[session_id]

    def reset(self, session_id: str) -> None:
        if session_id in self._instances:
            self._instances[session_id].reset()
            del self._instances[session_id]


def _load_generation_config() -> Dict[str, object] | None:
    raw_config = os.environ.get("ORCHESTRATOR_GENERATION_CONFIG")
    if not raw_config:
        return None
    try:
        config = json.loads(raw_config)
        if not isinstance(config, dict):
            raise ValueError("generation config must be a JSON object")
        return config
    except Exception as exc:  # pragma: no cover - defensive branch
        LOGGER.warning("Failed to parse ORCHESTRATOR_GENERATION_CONFIG: %s", exc)
        return None


MODEL_PATH = os.environ.get("FINE_TUNED_MODEL_PATH")
GENERATION_CONFIG = _load_generation_config()

_history_repo = ChatHistoryRepository()
_orchestrators = OrchestratorPool(MODEL_PATH, GENERATION_CONFIG)


@app.route("/", methods=["GET"])
def index() -> FlaskResponse:
    """Serve the landing page for ad-hoc manual testing."""
    return send_from_directory("templates", "index.html")


@app.route("/chat", methods=["POST"])
def chat() -> FlaskResponse:
    """Run the prompt orchestrator and persist the interaction."""
    try:
        body = request.get_json(silent=True) or {}
        user_input = str(body.get("message", ""))
        target_language = str(body.get("target_language", "en"))
        source_language = str(body.get("source_language", "auto"))
        if source_language.lower() == "auto":
            source_language = "en"
        session_id = str(body.get("session_id") or uuid.uuid4())

        orchestrator = _orchestrators.get(session_id)
        bot_response = orchestrator.run(user_input=user_input, target_language=target_language)

        _history_repo.append(
            session_id=session_id,
            user_input=user_input,
            bot_response=bot_response,
            source_language=source_language,
            target_language=target_language,
        )

        payload = {
            "response": bot_response,
            "session_id": session_id,
            "source_language": source_language,
            "target_language": target_language,
        }
        return jsonify(payload), 200
    except Exception as exc:  # pragma: no cover - defensive branch
        LOGGER.exception("Error processing /chat request")
        return jsonify({"error": str(exc)}), 500


@app.route("/text-to-speech", methods=["POST"])
def text_to_speech() -> FlaskResponse:
    """Return deterministic bytes that simulate a text-to-speech payload."""
    body = request.get_json(silent=True) or {}
    text = str(body.get("text", ""))
    fake_audio = b"ID3" + text.encode("utf-8")
    response = make_response(fake_audio)
    response.headers["Content-Type"] = "audio/mpeg"
    return response


@app.route("/chat-history/<session_id>", methods=["GET"])
def get_chat_history(session_id: str) -> FlaskResponse:
    history = _history_repo.get(session_id)
    return jsonify(history), 200


@app.route("/chat-history/<session_id>", methods=["DELETE"])
def reset_history(session_id: str) -> FlaskResponse:
    _orchestrators.reset(session_id)
    _history_repo.clear(session_id)
    return jsonify({"session_id": session_id, "cleared": True}), 200


if __name__ == "__main__":  # pragma: no cover - convenience for local debugging
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")), debug=True)
