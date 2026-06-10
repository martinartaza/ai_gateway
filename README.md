[![Español](https://img.shields.io/badge/idioma-español-red)](README.es.md)
[![English](https://img.shields.io/badge/lang-english-blue)](README.md)

# AI Gateway

Centralized AI service for internal use. Receives text, forwards it to a local language model, and returns the generated response. Contains no business logic or conversation memory — a stateless proxy reusable across multiple projects.

## How it works

```mermaid
sequenceDiagram
    participant C as Client<br/>(Magento / ERP / etc.)
    participant G as FastAPI<br/>AI Gateway
    participant DB as MySQL
    participant O as Ollama
    participant M as LLM Model<br/>(Qwen 2.5 3B)

    C->>G: POST /chat {system, prompt}
    G->>G: Validate API key
    G->>G: Apply rate limit
    G->>O: POST /v1/chat/completions
    O->>M: Inference
    M-->>O: Generated text
    O-->>G: {choices, usage}
    G->>DB: Log request + metrics
    G-->>C: {response, tokens, duration_ms}
```

Each consumer project builds its own prompts and maintains its own conversation history. The gateway only runs inference.

## Endpoints

| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| `POST` | `/chat` | API Key | Send a prompt to the model |
| `GET` | `/health` | — | Service and LLM status |
| `GET` | `/metrics` | Admin key | Daily usage statistics |

### POST /chat

```bash
curl -X POST https://ai.sebastianartaza.com/chat \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "system": "Extract ONLY the product name mentioned. Reply with the product name only, no explanations. If there is no product, reply: none.",
    "prompt": "Hi, do you have food for small dogs?",
    "temperature": 0.1,
    "max_tokens": 20
  }'
```

```json
{
  "response": "food for small dogs",
  "tokens": 38,
  "duration_ms": 201
}
```

#### Body parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `system` | string | Yes | — | Instruction defining the model's behavior |
| `prompt` | string | Yes | — | User message |
| `temperature` | float | No | `0.7` | Controls response creativity (see table below) |
| `max_tokens` | int | No | unlimited | Maximum number of tokens in the response |

#### temperature

Controls how deterministic or creative the model is. Lower values produce more focused and repeatable responses; higher values produce more varied and creative ones.

| Value | Behavior | Use for |
|-------|----------|---------|
| `0.1` | Near-deterministic | Entity extraction, classification |
| `0.2 – 0.4` | Tightly controlled | Structured responses, JSON, lists |
| `0.7` | Balanced (default) | General conversational assistant |
| `1.0 – 1.5` | Creative | Free-form text generation, ideas |

#### max_tokens

Limits the number of tokens (approximate words) the model can generate in its response. One token equals roughly 0.75 words in English.

Useful for extraction or classification tasks where the expected response is short — prevents the model from generating unnecessary explanations and reduces response time.

| Task | Suggested `max_tokens` |
|------|------------------------|
| Single entity extraction | `10 – 30` |
| Label classification | `5 – 15` |
| Short conversational reply | `100 – 200` |
| No restriction | omit the parameter |

### GET /health

```json
{
  "status": "ok",
  "model": "qwen2.5:3b",
  "llama_cpp": "running"
}
```

## Installation

### Requirements
- Docker with the Compose plugin
- `traefik` external network already created on the host

### Steps

```bash
# 1. Configure environment variables
cp .env.example .env
# Edit .env with your actual values

# 2. Start Ollama and download the model
docker compose up -d ollama
bash pull_model.sh

# 3. Start all services
docker compose up -d

# 4. Create MySQL tables (once only)
docker compose exec web python init_db.py
```

### Create a project (API key)

API keys are managed directly in MySQL:

```bash
docker compose exec mysql mysql -uroot -p ai_gateway -e \
  "INSERT INTO projects (name, api_key, enabled, rate_limit)
   VALUES ('project-name', 'secret-key-here', 1, '60/minute');"
```

## Changing the model

The gateway is model-agnostic. Ollama manages available models — to switch you only need to:

1. Stop the `web` container to avoid requests during the change
2. Delete the old model
3. Download the new model
4. Update `.env`
5. Restart everything

```bash
# 1. Stop web
docker compose stop web

# 2. Delete the old model
docker compose exec ollama ollama rm OLD_MODEL_NAME

# 3. Download the new model (~2 GB, may take a while)
docker compose exec ollama ollama pull NEW_MODEL_NAME

# 4. Update .env
LLM_MODEL_NAME=NEW_MODEL_NAME

# 5. Restart
docker compose up --build -d
```

### Available models with Ollama

| Model | `.env` `LLM_MODEL_NAME` | Approx. RAM | Best for |
|-------|------------------------|-------------|----------|
| Qwen 2.5 0.5B | `qwen2.5:0.5b` | ~600 MB | Extraction, simple classification |
| Qwen 2.5 1.5B | `qwen2.5:1.5b` | ~1.5 GB | Better comprehension, same speed |
| Qwen 2.5 3B *(current)* | `qwen2.5:3b` | ~2.5 GB | More elaborate responses, better reasoning |
| Llama 3.2 1B | `llama3.2:1b` | ~1.3 GB | Good alternative for English/Spanish |
| Llama 3.2 3B | `llama3.2:3b` | ~2.5 GB | Quality/speed balance |
| Mistral 7B | `mistral:7b` | ~5 GB | High quality (requires more RAM) |

> The target server has 8 GB of RAM. Models up to 3B run comfortably. Mistral 7B is the practical upper limit.

### Switching to an external API (Groq, OpenAI)

The `/v1/chat/completions` interface is compatible with any OpenAI-compatible provider. To use Groq for example:

```env
LLM_BASE_URL=https://api.groq.com/openai
LLM_MODEL_NAME=llama-3.1-8b-instant
```

And add the authentication header by editing `app/llm.py`:

```python
headers={"Authorization": f"Bearer {settings.llm_api_key}"}
```

Consumer projects require zero changes when migrating between models or providers.

## Environment variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | MySQL connection string | `mysql+pymysql://root:changeme@mysql/ai_gateway` |
| `MYSQL_ROOT_PASSWORD` | MySQL password (used by Docker) | — |
| `LLM_BASE_URL` | LLM backend base URL | `http://ollama:11434` |
| `LLM_MODEL_NAME` | Model name in Ollama | `qwen2.5:3b` |
| `LLM_NUM_CTX` | Context window in tokens (system + history + prompt). Qwen 2.5 3B supports up to 32768. | `8192` |
| `LLM_TIMEOUT` | Timeout in seconds for LLM calls. Increase for slow models or large contexts. | `120` |
| `DEFAULT_RATE_LIMIT` | Rate limit per API key | `60/minute` |
| `LOG_RETENTION_DAYS` | Days to retain logs | `30` |
| `LOG_LEVEL` | Log verbosity: `WARNING` \| `INFO` \| `DEBUG` | `WARNING` |
| `METRICS_API_KEY` | Key to access `/metrics` | — |

## Local development

```bash
# Activate virtual environment
workon ia_gateway

# Server with hot reload
uvicorn app.main:app --reload
```

## Tests

Tests use an in-memory SQLite database and mock the LLM — no MySQL or Ollama required.

```bash
workon ia_gateway

# All tests
pytest

# Specific file
pytest tests/test_chat.py -v

# Specific test
pytest tests/test_chat.py::test_chat_success -v

# Verbose output with prints
pytest -v -s

# Only tests that failed in the last run
pytest --lf
```
