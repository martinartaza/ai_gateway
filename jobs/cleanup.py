#!/usr/bin/env python3
"""Daily job: delete request logs older than LOG_RETENTION_DAYS.

Run via cron or manually:
    python -m jobs.cleanup
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.database import SessionLocal
from app.models import Request


def run(db=None) -> int:
    own_session = db is None
    if own_session:
        db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=settings.log_retention_days)
        deleted = db.query(Request).filter(Request.created_at < cutoff).delete()
        db.flush()
        if own_session:
            db.commit()
        print(f"Deleted {deleted} log entries older than {cutoff.date()}")
        return deleted
    except Exception:
        if own_session:
            db.rollback()
        raise
    finally:
        if own_session:
            db.close()


if __name__ == "__main__":
    run()
