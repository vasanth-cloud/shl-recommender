# SHL Assessment Recommender

FastAPI service for the SHL take-home assignment.

## Run locally

```bash
pip install -r requirements.txt
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Open the chat UI:

```text
http://127.0.0.1:8000/
```

## LLM ranking

The app uses the SHL catalog as the only source of recommendation URLs. It retrieves valid catalog candidates, then asks an OpenAI-compatible LLM to rerank the shortlist.

Set these environment variables before starting the server:

```bash
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

For OpenAI, `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `OPENAI_MODEL` also work. For Groq/OpenRouter, set `LLM_BASE_URL` and `LLM_MODEL` to the provider's OpenAI-compatible values.

If no key is configured or the LLM call fails, the service falls back to deterministic catalog scoring so the API still returns the required schema.
