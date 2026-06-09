import time

import httpx

from app.config import settings


async def generate(system: str, prompt: str) -> dict:
    payload = {
        "model": settings.llm_model_name,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    }
    t0 = time.monotonic()
    async with httpx.AsyncClient(base_url=settings.llm_base_url, timeout=60.0) as client:
        response = await client.post("/v1/chat/completions", json=payload)
        response.raise_for_status()
    duration_ms = int((time.monotonic() - t0) * 1000)

    data = response.json()
    usage = data.get("usage", {})
    return {
        "response": data["choices"][0]["message"]["content"],
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
        "duration_ms": duration_ms,
    }


async def health_check() -> bool:
    try:
        async with httpx.AsyncClient(base_url=settings.llm_base_url, timeout=5.0) as client:
            r = await client.get("/")
            return r.status_code == 200
    except httpx.HTTPError:
        return False
