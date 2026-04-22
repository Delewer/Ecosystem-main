from __future__ import annotations

from datetime import date
from typing import Optional

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from ..models import EventLog, SeasonalEvent, UserSeasonalProgress
from .audit_logger import log_event
from .service_result import BaseServiceResult

SETTING_POINTS_PER_LESSON = "ESTUDY_SEASONAL_POINTS_PER_LESSON"
DEFAULT_POINTS_PER_LESSON = 10

ERROR_MISSING_USER = "User is required"
ERROR_INVALID_POINTS = "Points must be positive"
ERROR_INACTIVE_EVENT = "Event is not active"
ERROR_MISSING_EVENT = "Event is required"

WARNING_NO_ACTIVE_EVENT = "no_active_event"
WARNING_ALREADY_COMPLETED = "already_completed"

SOURCE_LESSON_COMPLETION = "lesson_completion"


def _local_date(value) -> Optional[date]:
    if value is None:
        return None
    return timezone.localdate(value)


def _points_per_lesson() -> int:
    value = getattr(settings, SETTING_POINTS_PER_LESSON, DEFAULT_POINTS_PER_LESSON)
    try:
        return max(int(value), 1)
    except (TypeError, ValueError):
        return DEFAULT_POINTS_PER_LESSON


def _is_event_active(event: SeasonalEvent, today: date) -> bool:
    return bool(
        event and event.is_active and event.start_date <= today <= event.end_date
    )


def get_active_seasonal_event(*, today: Optional[date] = None) -> BaseServiceResult:
    current = today or timezone.localdate()
    event = (
        SeasonalEvent.objects.filter(
            is_active=True, start_date__lte=current, end_date__gte=current
        )
        .order_by("-start_date")
        .first()
    )
    if not event:
        return BaseServiceResult.ok(
            data={"event": None},
            warnings=[WARNING_NO_ACTIVE_EVENT],
        )
    return BaseServiceResult.ok(data={"event": event})


def enroll_user_in_active_event(
    *, user, today: Optional[date] = None
) -> BaseServiceResult:
    if user is None:
        return BaseServiceResult.fail(ERROR_MISSING_USER)
    result = get_active_seasonal_event(today=today)
    event = result.data.get("event")
    if event is None:
        return BaseServiceResult.ok(
            data={"progress": None},
            warnings=list(result.warnings),
        )
    progress, _ = UserSeasonalProgress.objects.get_or_create(user=user, event=event)
    return BaseServiceResult.ok(data={"progress": progress})


def record_seasonal_progress(
    *,
    user,
    points: int,
    source: str,
    event: SeasonalEvent | None = None,
    now=None,
    metadata: Optional[dict] = None,
) -> BaseServiceResult:
    if user is None:
        return BaseServiceResult.fail(ERROR_MISSING_USER)
    try:
        points_value = int(points)
    except (TypeError, ValueError):
        return BaseServiceResult.fail(ERROR_INVALID_POINTS)
    if points_value <= 0:
        return BaseServiceResult.fail(ERROR_INVALID_POINTS)

    now = now or timezone.now()
    today = _local_date(now) or timezone.localdate()

    if event is None:
        active_result = get_active_seasonal_event(today=today)
        event = active_result.data.get("event")
        if event is None:
            return BaseServiceResult.ok(
                data={"progress": None},
                warnings=list(active_result.warnings),
            )

    if not _is_event_active(event, today):
        return BaseServiceResult.fail(ERROR_INACTIVE_EVENT)

    with transaction.atomic():
        progress, _ = UserSeasonalProgress.objects.select_for_update().get_or_create(
            user=user, event=event
        )
        if progress.completed_at:
            return BaseServiceResult.ok(
                data={"progress": progress, "completed": True},
                warnings=[WARNING_ALREADY_COMPLETED],
            )

        progress.points += points_value
        completed_now = progress.points >= event.points_goal
        if completed_now:
            progress.completed_at = now
        progress.save(update_fields=["points", "completed_at", "updated_at"])

    event_metadata = {
        "event_id": event.id,
        "event_slug": event.slug,
        "source": source,
        "points_added": points_value,
        "total_points": progress.points,
        "points_goal": event.points_goal,
    }
    if metadata:
        event_metadata.update(metadata)
    log_event(EventLog.EVENT_SEASONAL_PROGRESS, user=user, metadata=event_metadata)

    awarded_xp = 0
    if completed_now and event.reward_xp > 0:
        profile = getattr(user, "userprofile", None)
        if profile:
            profile.add_xp(event.reward_xp, reason=f"Seasonal event {event.title}")
            awarded_xp = event.reward_xp
        log_event(
            EventLog.EVENT_SEASONAL_COMPLETED,
            user=user,
            metadata={
                "event_id": event.id,
                "event_slug": event.slug,
                "reward_xp": event.reward_xp,
                "total_points": progress.points,
            },
        )

    return BaseServiceResult.ok(
        data={
            "progress": progress,
            "completed": completed_now,
            "awarded_xp": awarded_xp,
        }
    )


def record_seasonal_progress_for_lesson(*, user, lesson) -> BaseServiceResult:
    metadata = {"lesson_id": getattr(lesson, "id", None)}
    return record_seasonal_progress(
        user=user,
        points=_points_per_lesson(),
        source=SOURCE_LESSON_COMPLETION,
        metadata=metadata,
    )
