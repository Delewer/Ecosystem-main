"""
Audit trail helpers for teacher/admin dashboards.
"""

from datetime import datetime
from typing import Iterable, Optional

from ..models import EventLog, Lesson, User


def filter_events(
    *,
    users: Optional[Iterable[User]] = None,
    event_types: Optional[Iterable[str]] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> list[EventLog]:
    """
    Return event logs filtered by user(s), event types, and date range.
    """
    qs = EventLog.objects.all()
    if users:
        user_ids = [u.id for u in users]
        qs = qs.filter(user_id__in=user_ids)
    if event_types:
        qs = qs.filter(event_type__in=list(event_types))
    if start:
        qs = qs.filter(created_at__gte=start)
    if end:
        qs = qs.filter(created_at__lte=end)
    return list(qs.select_related("user").order_by("-created_at")[:500])


def recent_lesson_views(lesson: Lesson, limit: int = 100) -> list[EventLog]:
    """Return recent lesson_view events for a lesson."""
    return list(
        EventLog.objects.filter(
            event_type=EventLog.EVENT_LESSON_VIEW, metadata__lesson_id=lesson.id
        )
        .select_related("user")
        .order_by("-created_at")[:limit]
    )
