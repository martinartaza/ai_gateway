from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project

_bearer = HTTPBearer()


def get_project(
    credentials: HTTPAuthorizationCredentials = Security(_bearer),
    db: Session = Depends(get_db),
) -> Project:
    project = (
        db.query(Project)
        .filter(Project.api_key == credentials.credentials, Project.enabled.is_(True))
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or disabled API key",
        )
    return project
