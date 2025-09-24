# Multilingual Support Chatbot

A Flask-powered multilingual chatbot that integrates custom fine-tuned language models from Hugging Face Transformers and prompt orchestration powered by LangChain. The service enables multilingual conversations and provides lightweight endpoints suitable for experimentation or container-based deployment.

## Team Members

- Keshav Anand Singh (300988081)
- Blessing Akintonde (301264139)
- Cole Ramsey (301333287)
- Nicholas Laprade (301266745)
- Ali Al-gharibawi (301238399)

## Project Overview

The chatbot exposes REST endpoints through a Flask application while delegating language understanding to a LangChain-powered prompt orchestrator. Fine-tuning scripts and sample datasets are provided to adapt Hugging Face causal language models (for example GPT-2 derivatives) to your domain. The trained model can be loaded at runtime by setting the `FINE_TUNED_MODEL_PATH` environment variable.

## Features

- Hugging Face fine-tuning script for causal language models
- LangChain prompt orchestration with conversation memory per session
- REST API for chat, chat history, and placeholder text-to-speech responses
- Vite-powered React prototype for user-facing conversations
- Sample multilingual dataset for experimentation

## Technical Stack

- Flask + Flask-Cors for the HTTP API
- Hugging Face Transformers, Datasets, and Accelerate for model training
- LangChain for prompt orchestration and conversation memory
- PyTest for automated testing

## Prerequisites

- AWS Account with appropriate permissions
- Python 3.8+
- AWS CLI configured
- Flask


- Node.js 18+ and npm (required to build or run the React prototype)

## Setup Instructions

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   Installing `requirements.txt` covers the Python backend only. To run the prototype UI you must also install the frontend dependencies:
   ```bash
   cd frontend
   npm install
   cd ..
   ```
3. (Optional) Export `FINE_TUNED_MODEL_PATH` to point to your trained model directory.
4. Start the application locally:
   ```bash
   flask --app app run --port 8000
   ```

### Local development

Run the API locally with Flask:

```bash
flask --app app run --port 8000
```

Execute the unit test suite:

```bash
pytest
```

Launch the React prototype to test the experience end-to-end:

```bash
cd frontend
npm install
npm run dev -- --host
```

The Vite dev server runs on [http://localhost:5173](http://localhost:5173) and proxies requests to the Flask API running on port 8000. Set `VITE_API_BASE_URL` in a `.env` file to target a different backend.


## Fine-tuning a language model

Use the provided script to fine-tune a causal language model on a JSONL dataset:

```bash
python scripts/fine_tune_model.py \
  --model-name-or-path distilgpt2 \
  --dataset-path data/multilingual_chat_dataset.jsonl \
  --output-dir models/fine_tuned
```

The script relies on the Hugging Face `Trainer` API, supports optional evaluation splits, and saves the model/tokenizer to the specified directory. Set `FINE_TUNED_MODEL_PATH` to the resulting directory so the Flask app loads it at startup. When no path is supplied, the application falls back to a lightweight template-based responder, keeping local development lightweight.

## Prompt orchestration

`ml/orchestrator.py` defines the `PromptOrchestrator` which wires LangChain's `LLMChain`, `PromptTemplate`, and `ConversationBufferMemory` together. The orchestrator keeps a dedicated memory per session so the chatbot can respond with awareness of prior turns. When a fine-tuned model path is available, the orchestrator streams requests through a Hugging Face text-generation pipeline; otherwise it uses a deterministic fallback implementation to remain test friendly.

## Project Structure

```
├── README.md
├── requirements.txt
├── app.py
├── tests/
└── docs/
```

Additional assets:

- `frontend/`: Vite + React prototype with components tailored to the API responses.
- `docs/deployment.md`: Wiki-style runbooks that describe local setup, AWS deployment, and frontend publishing steps.

## Estimated Costs

- AWS Lambda: $0.20 per 1 million requests
- Amazon Lex: $4 per 1,000 speech requests / $0.75 per 1,000 text requests
- Amazon Translate: $15 per 1 million characters
- Amazon Polly: $4 per 1 million characters
- AWS DynamoDB: Free tier includes 25GB, then ~$0.25 per GB/month
- AWS CloudWatch: ~$0.50 per GB of log storage

## License

This project is part of COMP 264: Cloud Machine Learning course at Ryerson University.
