# Multilingual Chatbot API Documentation

## Overview

This API provides endpoints for a multilingual chatbot that supports text translation and text-to-speech capabilities using AWS services.

## Base URL

```
https://[api-id].execute-api.[region].amazonaws.com/[stage]
```

## Endpoints

### 1. Chat Endpoint

Process user messages and return responses in the specified language.

**Endpoint:** `POST /chat`

**Request Body:**

```json
{
  "message": "Hello, how are you?",
  "source_language": "en",
  "target_language": "es",
  "session_id": "user123"
}
```

**Parameters:**

- `message` (string): The user's input message
- `source_language` (string): Language code of the input message (e.g., "en", "es", "fr")
- `target_language` (string): Desired language for the response
- `session_id` (string): Unique identifier for the chat session

**Response:**

```json
{
  "response": "Hola, ¿cómo estás?",
  "source_language": "en",
  "target_language": "es"
}
```

### 2. Text-to-Speech Endpoint

Convert text to speech in the specified language and voice.

**Endpoint:** `POST /text-to-speech`

**Request Body:**

```json
{
  "text": "Hello world",
  "language_code": "en-US",
  "voice_id": "Joanna"
}
```

**Parameters:**

- `text` (string): Text to convert to speech
- `language_code` (string): Language code for the text (e.g., "en-US", "es-ES")
- `voice_id` (string): AWS Polly voice ID (e.g., "Joanna", "Matthew")

**Response:**

- Content-Type: audio/mpeg
- Body: MP3 audio stream

### 3. Chat History Endpoint

Retrieve chat history for a specific session.

**Endpoint:** `GET /chat-history/{session_id}`

**Parameters:**

- `session_id` (path parameter): Unique identifier for the chat session

**Response:**

```json
[
  {
    "session_id": "user123",
    "timestamp": "2024-03-21T10:30:00",
    "user_input": "Hello",
    "bot_response": "Hola",
    "source_language": "en",
    "target_language": "es"
  }
]
```

## Error Responses

All endpoints may return the following error responses:

**400 Bad Request:**

```json
{
  "error": "Invalid request parameters"
}
```

**500 Internal Server Error:**

```json
{
  "error": "Internal server error message"
}
```

## Supported Languages

The chatbot supports the following languages:

- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- Chinese (zh)
- Japanese (ja)
- Korean (ko)

## Rate Limits

- 100 requests per minute per IP address
- 1000 requests per hour per session_id

## Authentication

All endpoints require AWS IAM authentication. Include your AWS credentials in the request headers:

```
Authorization: AWS4-HMAC-SHA256 Credential=[access-key]/[date]/[region]/[service]/aws4_request
```
