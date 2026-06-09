from datetime import datetime, timedelta

from app.models import Project, Request as RequestLog
from jobs.cleanup import run


def _make_log(project_id, prompt, days_ago=0):
    return RequestLog(
        project_id=project_id,
        ip="127.0.0.1",
        prompt=prompt,
        response="resp",
        duration_ms=100,
        prompt_tokens=5,
        completion_tokens=3,
        created_at=datetime.utcnow() - timedelta(days=days_ago),
    )


def test_cleanup_deletes_old_logs(db, project):
    old = _make_log(project.id, "old-prompt", days_ago=31)
    recent = _make_log(project.id, "recent-prompt", days_ago=0)
    db.add_all([old, recent])
    db.flush()

    deleted = run(db=db)

    assert deleted == 1
    remaining = db.query(RequestLog).filter_by(project_id=project.id).all()
    assert len(remaining) == 1
    assert remaining[0].prompt == "recent-prompt"


def test_cleanup_keeps_logs_within_retention(db, project):
    log = _make_log(project.id, "borderline", days_ago=29)
    db.add(log)
    db.flush()

    deleted = run(db=db)

    assert deleted == 0


def test_cleanup_returns_zero_when_nothing_to_delete(db, project):
    deleted = run(db=db)
    assert deleted == 0
