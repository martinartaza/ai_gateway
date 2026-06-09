import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app import llm
from app.auth import get_project
from app.config import settings
from app.database import get_db
from app.models import Project
from app.models import Request as RequestLog
from app.rate_limit import limiter
from app.schemas import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
@limiter.limit(settings.default_rate_limit)
async def chat(
    body: ChatRequest,
    request: Request,
    project: Project = Depends(get_project),
    db: Session = Depends(get_db),
) -> ChatResponse:
    result = None
    try:
        result = await llm.generate(body.system, body.prompt, body.temperature, body.max_tokens)
        return ChatResponse(
            response=result["response"],
            tokens=result["prompt_tokens"] + result["completion_tokens"],
            duration_ms=result["duration_ms"],
        )
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM backend unavailable",
        )
    finally:
        try:
            log = RequestLog(
                project_id=project.id,
                ip=request.client.host,
                prompt=body.prompt,
                response=result["response"] if result else None,
                duration_ms=result["duration_ms"] if result else None,
                prompt_tokens=result["prompt_tokens"] if result else None,
                completion_tokens=result["completion_tokens"] if result else None,
            )
            db.add(log)
            db.commit()
        except Exception:
            db.rollback()
