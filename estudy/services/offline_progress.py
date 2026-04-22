from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from ..models import EventLog, LessonProgress, OfflineProgressQueue
from .audit_logger import log_event
from .service_result import BaseServiceResult

ERROR_MISSING_ENTRY = "Offline queue entry is required"
ERROR_INVALID_PAYLOAD = "Offline payload is invalid"
ERROR_UNKNOWN_KIND = "Offline payload kind is unsupported"
ERROR_MISSING_COMPLETED = "Completed flag is required"
ERROR_INVALID_COMPLETED = "Completed flag is invalid"
ERROR_INVALID_LIMIT = "Limit must be a positive integer"

WARNING_INVALID_COMPLETED_AT = "invalid_completed_at"
WARNING_LIMIT_CLAMPED = "limit_clamped"

ACTION_APPLIED = "applied"
ACTION_SKIPPED = "skipped"
ACTION_CONFLICT = "conflict"

CONFLICT_POLICY_LATEST_COMPLETION = "latest_completion"

KIND_LESSON_PROGRESS = "lesson_progress"
PAYLOAD_KIND = "kind"
PAYLOAD_COMPLETED = "completed"
PAYLOAD_COMPLETED_AT = "completed_at"
PAYLOAD_SECONDS_SPENT = "seconds_spent"
PAYLOAD_POINTS_EARNED = "points_earned"

TRUE_VALUES = {"true", "1", "yes"}
FALSE_VALUES = {"false", "0", "no"}

DEFAULT_BATCH_LIMIT = 100
MIN_BATCH_LIMIT = 1
MAX_BATCH_LIMIT = 500


@dataclass(frozen=True)
class OfflineProgressSnapshot:
    action: str
    conflict: bool
    progress_id: int | None
    offline_completed_at: Optional[datetime]
    server_completed_at: Optional[datetime]
    points_earned: int | None
    fastest_completion_seconds: int | None


def _normalize_bool(value) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in TRUE_VALUES:
        return True
    if text in FALSE_VALUES:
        return False
    return None


def _parse_completed_at(value) -> tuple[Optional[datetime], list[str]]:
    warnings: list[str] = []
    if value is None:
        return None, warnings
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = parse_datetime(str(value))
    if parsed is None:
        warnings.append(WARNING_INVALID_COMPLETED_AT)
        return None, warnings
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed, warnings


def _normalize_int(value) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_limit(limit: Optional[int]) -> tuple[Optional[int], list[str]]:
    if limit is None:
        return None, []
    try:
        value = int(limit)
    except (TypeError, ValueError):
        raise ValueError(ERROR_INVALID_LIMIT)
    if value < MIN_BATCH_LIMIT:
        raise ValueError(ERROR_INVALID_LIMIT)
    warnings = []
    if value > MAX_BATCH_LIMIT:
        value = MAX_BATCH_LIMIT
        warnings.append(WARNING_LIMIT_CLAMPED)
    return value, warnings


def _log_sync_event(
    *,
    event_type: str,
    entry: OfflineProgressQueue,
    metadata: dict,
) -> None:
    payload = {
        "entry_id": entry.id,
        "lesson_id": entry.lesson_id,
        "policy": CONFLICT_POLICY_LATEST_COMPLETION,
    }
    payload.update(metadata)
    log_event(event_type, user=entry.user, metadata=payload)


def apply_offline_progress_entry(
    *,
    entry: OfflineProgressQueue,
    now=None,
) -> BaseServiceResult:
    if entry is None:
        return BaseServiceResult.fail(ERROR_MISSING_ENTRY)
    payload = entry.payload
    if not isinstance(payload, dict):
        return BaseServiceResult.fail(ERROR_INVALID_PAYLOAD)

    kind = payload.get(PAYLOAD_KIND, KIND_LESSON_PROGRESS)
    if kind != KIND_LESSON_PROGRESS:
        return BaseServiceResult.fail(ERROR_UNKNOWN_KIND)

    completed_value = payload.get(PAYLOAD_COMPLETED)
    if completed_value is None:
        return BaseServiceResult.fail(ERROR_MISSING_COMPLETED)
    completed = _normalize_bool(completed_value)
    if completed is None:
        return BaseServiceResult.fail(ERROR_INVALID_COMPLETED)

    now = now or timezone.now()
    offline_completed_at, warnings = _parse_completed_at(
        payload.get(PAYLOAD_COMPLETED_AT)
    )
    if completed and offline_completed_at is None:
        offline_completed_at = entry.created_at or now

    progress = LessonProgress.objects.filter(
        user=entry.user, lesson=entry.lesson
    ).first()
    server_completed_at = progress.completed_at if progress else None

    action = ACTION_SKIPPED
    conflict = False
    update_fields: list[str] = []
    points_earned = None
    fastest_completion_seconds = None

    if completed:
        if progress is None:
            progress = LessonProgress.objects.create(
                user=entry.user, lesson=entry.lesson
            )
            server_completed_at = progress.completed_at
        if progress.completed and server_completed_at and offline_completed_at:
            if offline_completed_at <= server_completed_at:
                action = ACTION_CONFLICT
                conflict = True
            else:
                action = ACTION_APPLIED
        else:
            action = ACTION_APPLIED

        if action == ACTION_APPLIED:
            if not progress.completed:
                progress.completed = True
                update_fields.append("completed")
            if offline_completed_at and (
                server_completed_at is None
                or offline_completed_at > server_completed_at
            ):
                progress.completed_at = offline_completed_at
                update_fields.append("completed_at")

            points_value = _normalize_int(payload.get(PAYLOAD_POINTS_EARNED))
            if points_value is not None and points_value > progress.points_earned:
                progress.points_earned = points_value
                update_fields.append("points_earned")
                points_earned = points_value

            seconds_value = _normalize_int(payload.get(PAYLOAD_SECONDS_SPENT))
            if seconds_value is not None and seconds_value > 0:
                if (
                    progress.fastest_completion_seconds == 0
                    or seconds_value < progress.fastest_completion_seconds
                ):
                    progress.fastest_completion_seconds = seconds_value
                    update_fields.append("fastest_completion_seconds")
                    fastest_completion_seconds = seconds_value

            if update_fields:
                update_fields.append("updated_at")
                progress.save(update_fields=update_fields)

            _log_sync_event(
                event_type=EventLog.EVENT_OFFLINE_PROGRESS_SYNC,
                entry=entry,
                metadata={
                    "action": action,
                    "offline_completed_at": (
                        offline_completed_at.isoformat()
                        if offline_completed_at
                        else None
                    ),
                    "server_completed_at": (
                        server_completed_at.isoformat() if server_completed_at else None
                    ),
                },
            )
        elif action == ACTION_CONFLICT:
            _log_sync_event(
                event_type=EventLog.EVENT_OFFLINE_PROGRESS_CONFLICT,
                entry=entry,
                metadata={
                    "action": action,
                    "offline_completed_at": (
                        offline_completed_at.isoformat()
                        if offline_completed_at
                        else None
                    ),
                    "server_completed_at": (
                        server_completed_at.isoformat() if server_completed_at else None
                    ),
                },
            )

    entry.synced = True
    entry.synced_at = now
    entry.save(update_fields=["synced", "synced_at"])

    snapshot = OfflineProgressSnapshot(
        action=action,
        conflict=conflict,
        progress_id=progress.id if progress else None,
        offline_completed_at=offline_completed_at,
        server_completed_at=server_completed_at,
        points_earned=points_earned,
        fastest_completion_seconds=fastest_completion_seconds,
    )
    return BaseServiceResult.ok(data={"snapshot": snapshot}, warnings=warnings)


def process_offline_progress_queue(*, limit: Optional[int] = None) -> BaseServiceResult:
    try:
        limit_value, warnings = _normalize_limit(limit)
    except ValueError as exc:
        return BaseServiceResult.fail(str(exc))

    queryset = OfflineProgressQueue.objects.filter(synced=False).order_by("created_at")
    if limit_value is not None:
        queryset = queryset[:limit_value]

    processed = 0
    synced = 0
    failed = 0

    for entry in queryset:
        processed += 1
        result = apply_offline_progress_entry(entry=entry)
        if result.success:
            synced += 1
        else:
            failed += 1

    return BaseServiceResult.ok(
        data={"processed": processed, "synced": synced, "failed": failed},
        warnings=warnings,
    )
