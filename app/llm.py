import logging
import time

import httpx

from app.config import settings

logger = logging.getLogger("ai_gateway.llm")


async def generate(
    system: str,
    prompt: str,
    temperature: float = 0.7,
    max_tokens: int | None = None,
) -> dict:
    payload = {
        "model": settings.llm_model_name,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    logger.info(
        "LLM REQUEST | model=%s | system_chars=%d | prompt_chars=%d | max_tokens=%s",
        settings.llm_model_name, len(system), len(prompt), max_tokens,
    )
    t0 = time.monotonic()
    try:
        async with httpx.AsyncClient(base_url=settings.llm_base_url, timeout=60.0) as client:
            response = await client.post("/v1/chat/completions", json=payload)
            response.raise_for_status()
    except httpx.TimeoutException as e:
        logger.error("LLM TIMEOUT | elapsed=%.1fs | %s", time.monotonic() - t0, e)
        raise
    except httpx.HTTPStatusError as e:
        logger.error("LLM HTTP ERROR | status=%d | body=%s", e.response.status_code, e.response.text[:500])
        raise
    except httpx.HTTPError as e:
        logger.error("LLM CONNECTION ERROR | %s: %s", type(e).__name__, e)
        raise
    duration_ms = int((time.monotonic() - t0) * 1000)
    logger.info("LLM RESPONSE | duration_ms=%d", duration_ms)

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
