# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI AI Gateway — a lightweight, stateless, centralized AI service that exposes a single API for multiple internal projects to consume. It receives text, forwards it to a local LLM via llama.cpp, and returns the generated response. It contains **no business logic, no conversation memory, and no project-specific knowledge**.

## Virtual Environment

Python virtual environment: `ia_gateway` (managed with `virtualenvwrapper`)

```bash
workon ia_gateway
```

Already installed: `fastapi`, `uvicorn`, `httpx`, `pydantic`, `pymupdf`

## Commands

```bash
# Run dev server
uvicorn app.main:app --reload

# Run tests (SQLite in-memory, no MySQL or llama.cpp needed)
pytest

# Run a single test
pytest tests/test_chat.py::test_function_name -v

# Create tables in MySQL (run once before first startup)
python init_db.py
```

## Docker

```bash
# 1. Copy and fill .env
cp .env.example .env

# 2. Start Ollama first and pull the model (~400 MB, once only)
docker compose up -d ollama
bash pull_model.sh

# 3. Start everything
docker compose up -d

# 4. Create MySQL tables (once only)
python init_db.py

# Logs
docker compose logs -f web
docker compose logs -f ollama
```

The `traefik` network must already exist on the host (shared with all projects).  
`backend` is project-scoped (created automatically as `ai_gateway_backend`) — no conflict with other projects.  
Services communicate via internal hostnames: `mysql:3306` and `ollama:11434`.

## Target Infrastructure

- **Server**: Hetzner Cloud, 4 vCPU / 8 GB RAM / 80 GB SSD
- **OS**: Ubuntu Server + Nginx
- **LLM runtime**: llama.cpp + Qwen 2.5 0.5B (GGUF format)
- **DB**: MySQL

## Architecture

```
Client → FastAPI → llama.cpp → Qwen 0.5B
```

FastAPI handles: API key validation, rate limiting, logging/metrics, forwarding prompts to llama.cpp, returning responses.

FastAPI does NOT handle: conversation history, session management, business logic, external system access.

**Consumer projects** are responsible for building prompts, maintaining conversation history, and all domain logic.

## API

### POST /chat
```
Authorization: Bearer API_KEY

Body:  { "system": "...", "prompt": "..." }
Reply: { "response": "...", "tokens": 45, "duration_ms": 320 }
```

### GET /health
```json
{ "status": "ok", "model": "qwen2.5-0.5b", "llama_cpp": "running" }
```

### GET /metrics
Returns requests/day, requests/project, avg response time, tokens consumed, errors. Admin access only.

## Database Schema

**`projects`** — one row per consumer project  
`id, name, api_key, enabled, created_at`

**`requests`** — one row per API call  
`id, created_at, project_id, ip, prompt, response, duration_ms, prompt_tokens, completion_tokens`

Scheduled daily job deletes records older than 30 days (configurable).

## Key Design Constraints

- **Stateless**: every request must carry all context needed — no sessions, no history reconstruction.
- **Model-agnostic interface**: the `/chat` contract must not change when swapping backends (Qwen 1.5B, Qwen 4B, Groq, OpenAI, etc.). Consumer projects must require zero changes on model migration.
- **Rate limiting**: per API key, default 60 req/min, configurable per project.
- **Model scope**: Qwen 0.5B is for entity extraction, classification, basic NLU, and simple response generation — not coding, reasoning, or general knowledge.
