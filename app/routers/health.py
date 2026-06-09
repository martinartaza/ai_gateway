from fastapi import APIRouter

from app import llm
from app.config import settings
from app.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    llama_status = "running" if await llm.health_check() else "unavailable"
    return HealthResponse(
        status="ok",
        model=settings.llm_model_name,
        llama_cpp=llama_status,
    )
