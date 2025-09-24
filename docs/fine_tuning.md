# Fine-tuning workflow

The project ships with a minimal dataset (`data/multilingual_chat_dataset.jsonl`) and the `scripts/fine_tune_model.py` CLI helper. The script uses the Hugging Face `Trainer` and can be adapted for larger datasets or different base models.

## Prepare the environment

```bash
pip install -r requirements.txt
pip install torch --extra-index-url https://download.pytorch.org/whl/cpu
```

## Run the trainer

```bash
python scripts/fine_tune_model.py \
  --model-name-or-path distilgpt2 \
  --dataset-path data/multilingual_chat_dataset.jsonl \
  --output-dir models/fine_tuned \
  --epochs 1 \
  --batch-size 2
```

At the end of training the directory `models/fine_tuned` will contain the model weights and tokenizer artefacts.

## Load the model in the API

Set the path as an environment variable before starting Flask:

```bash
export FINE_TUNED_MODEL_PATH=$(pwd)/models/fine_tuned
flask --app app run --port 8000
```

Each incoming chat request uses a dedicated `PromptOrchestrator` instance so conversation history and LangChain memory do not bleed across sessions. The orchestrator falls back to a deterministic responder when a trained model is not available, enabling tests and CI pipelines to run quickly.
