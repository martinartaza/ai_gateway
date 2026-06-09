from pydantic import BaseModel, field_validator


class ChatRequest(BaseModel):
    system: str
    prompt: str
    temperature: float = 0.7
    max_tokens: int | None = None

    @field_validator("system", "prompt")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be empty")
        return v

    @field_validator("temperature")
    @classmethod
    def valid_temperature(cls, v: float) -> float:
        if not 0.0 <= v <= 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0")
        return v


class ChatResponse(BaseModel):
    response: str
    tokens: int
    duration_ms: int


class HealthResponse(BaseModel):
    status: str
    model: str
    llama_cpp: str


class MetricsSummary(BaseModel):
    requests_today: int
    requests_by_project: dict
    avg_duration_ms: float
    total_tokens: int
    errors_today: int
