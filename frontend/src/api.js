const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function parseJson(response) {
  const text = await response.text();
  try {
    return text ? JSON.parse(text) : {};
  } catch (error) {
    throw new Error('Received an invalid JSON response from the API.');
  }
}

export async function postChatMessage({ sessionId, message, sourceLanguage, targetLanguage }) {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      source_language: sourceLanguage,
      target_language: targetLanguage,
      session_id: sessionId || undefined
    })
  });

  if (!response.ok) {
    const errorPayload = await parseJson(response);
    const detail = errorPayload?.error || response.statusText;
    throw new Error(`Chat request failed: ${detail}`);
  }

  return parseJson(response);
}

export async function getChatHistory(sessionId) {
  const response = await fetch(`${API_BASE_URL}/chat-history/${sessionId}`);

  if (!response.ok) {
    if (response.status === 404) {
      return [];
    }
    const errorPayload = await parseJson(response);
    const detail = errorPayload?.error || response.statusText;
    throw new Error(`Unable to load chat history: ${detail}`);
  }

  return parseJson(response);
}

export async function resetChatHistory(sessionId) {
  const response = await fetch(`${API_BASE_URL}/chat-history/${sessionId}`, {
    method: 'DELETE'
  });

  if (!response.ok) {
    const errorPayload = await parseJson(response);
    const detail = errorPayload?.error || response.statusText;
    throw new Error(`Unable to reset chat history: ${detail}`);
  }

  return parseJson(response);
}

export { API_BASE_URL };
