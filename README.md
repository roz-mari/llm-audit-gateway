# LLM Audit Gateway

A small API that sits in front of an LLM. I built it while learning Python and FastAPI.

My day to day stack is TypeScript and Java. At work I integrate AI agents into SaaS products,
and I wanted to understand the backend side better: how to control who calls the model,
what data is sent to it, and how to keep a record of every request.

## What it does

- **API keys**: every request needs an `X-API-Key` header. Keys are stored as SHA256 hashes, not in plain text.
- **Redaction**: emails and secret keys are removed from the prompt before it is sent to the model.
- **Tool calling**: the model can call a `get_current_time` tool. The gateway runs it and sends the result back.
- **Audit log**: every request is saved in PostgreSQL (prompt after redaction, answer, tools used, tokens, latency, status).
- Each API key can only read its own logs.

Works with any OpenAI compatible API (OpenAI, Ollama, vLLM...).

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/v1/ask` | Send a question to the model |
| GET | `/v1/logs` | Last requests for your API key |

Swagger docs: http://localhost:8000/docs

## Run locally

```bash
cp .env.example .env    # set your LLM provider and key
docker compose up --build

# create an API key
docker compose exec api python -m scripts.create_api_key "my laptop"
```

```bash
curl -X POST http://localhost:8000/v1/ask \
  -H "X-API-Key: gw_..." \
  -H "Content-Type: application/json" \
  -d '{"question": "What time is it in Tokyo? My email is me@example.com"}'
```

```json
{
  "answer": "It is 21:14 in Tokyo.",
  "tools_used": ["get_current_time"],
  "redactions": ["email"]
}
```

To run it for free, you can use a local model with [Ollama](https://ollama.com)
and set `LLM_BASE_URL=http://host.docker.internal:11434/v1`.

## Tests

```bash
pip install -r requirements.txt
pytest
```

The tests use SQLite and a fake LLM client, so they don't need a database or an API key.

## TODO

- [ ] Alembic migrations
- [ ] Rate limiting per API key
- [ ] Streaming responses

## Stack

Python, FastAPI, SQLAlchemy, PostgreSQL, OpenAI SDK, pytest, Docker, GitHub Actions
