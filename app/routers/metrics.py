from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Project
from app.models import Request as RequestLog
from app.schemas import MetricsSummary

router = APIRouter()
_bearer = HTTPBearer()


def _require_admin(
    credentials: HTTPAuthorizationCredentials = Security(_bearer),
) -> None:
    if credentials.credentials != settings.metrics_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )


@router.get("/metrics", response_model=MetricsSummary, dependencies=[Depends(_require_admin)])
def metrics(db: Session = Depends(get_db)) -> MetricsSummary:
    today = datetime.utcnow().date()
    start_of_day = datetime(today.year, today.month, today.day)

    requests_today = (
        db.query(func.count(RequestLog.id))
        .filter(RequestLog.created_at >= start_of_day)
        .scalar() or 0
    )

    by_project = (
        db.query(Project.name, func.count(RequestLog.id))
        .join(RequestLog, RequestLog.project_id == Project.id)
        .filter(RequestLog.created_at >= start_of_day)
        .group_by(Project.id, Project.name)
        .all()
    )

    avg_duration = (
        db.query(func.avg(RequestLog.duration_ms))
        .filter(
            RequestLog.created_at >= start_of_day,
            RequestLog.duration_ms.isnot(None),
        )
        .scalar() or 0.0
    )

    total_tokens = (
        db.query(func.sum(RequestLog.prompt_tokens + RequestLog.completion_tokens))
        .filter(RequestLog.created_at >= start_of_day)
        .scalar() or 0
    )

    errors_today = (
        db.query(func.count(RequestLog.id))
        .filter(
            RequestLog.created_at >= start_of_day,
            RequestLog.response.is_(None),
        )
        .scalar() or 0
    )

    return MetricsSummary(
        requests_today=requests_today,
        requests_by_project={name: count for name, count in by_project},
        avg_duration_ms=float(avg_duration),
        total_tokens=int(total_tokens),
        errors_today=errors_today,
    )
