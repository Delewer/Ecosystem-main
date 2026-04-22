"""
Audit logging helpers for platform events.
"""

from typing import Any, Dict

from django.conf import settings

from ..models import EventLog
from .audit_trail_immutable import append_audit_entry


def log_event(
    event_type: str, *, user=None, metadata: Dict[str, Any] | None = None
) -> EventLog:
    """
    Create an event log entry.
    """
    event = EventLog.objects.create(
        user=user,
        event_type=event_type,
        metadata=metadata or {},
    )
    if getattr(settings, "ESTUDY_AUDIT_TRAIL_ENABLED", True):
        append_audit_entry(
            event_type=event.event_type,
            user=event.user,
            metadata=event.metadata,
            created_at=event.created_at,
        )
    return event
