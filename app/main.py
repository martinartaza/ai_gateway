import json
import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.rate_limit import limiter
from app.routers import chat, health, metrics


class UTF8JSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(content, ensure_ascii=False).encode("utf-8")


logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.WARNING),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)

app = FastAPI(title="AI Gateway", default_response_class=UTF8JSONResponse)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(chat.router)
app.include_router(health.router)
app.include_router(metrics.router)
