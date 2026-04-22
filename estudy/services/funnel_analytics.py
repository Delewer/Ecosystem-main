from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from django.db.models import Min

from ..models import EventLog
from .service_result import BaseServiceResult

PERCENT_MIN = 0.0
PERCENT_MAX = 100.0
SCORE_DECIMALS = 2

DEFAULT_INCLUDE_ANONYMOUS = False
DEFAULT_REQUIRE_ORDER = False

UNKNOWN_STEP_WARNING = "unknown_steps"
ANONYMOUS_GROUPED_WARNING = "anonymous_users_grouped"


@dataclass(frozen=True)
class FunnelStepSnapshot:
    step: str
    user_count: int
    conversion_rate: float
    drop_off: int
    drop_off_rate: float


def _round_percent(value: float) -> float:
    return round(value, SCORE_DECIMALS)


def _safe_percent(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return PERCENT_MIN
    return _round_percent((numerator / denominator) * PERCENT_MAX)


def _collect_step_users(steps: Iterable[str], queryset) -> dict[str, set[int | None]]:
    step_users = {step: set() for step in steps}
    for event_type, user_id in queryset.values_list("event_type", "user_id").distinct():
        if event_type in step_users:
            step_users[event_type].add(user_id)
    return step_users


def _collect_step_times(
    steps: Iterable[str], queryset
) -> dict[str, dict[int | None, object]]:
    step_times: dict[str, dict[int | None, object]] = {}
    for step in steps:
        entries = (
            queryset.filter(event_type=step)
            .values_list("user_id")
            .annotate(first=Min("created_at"))
        )
        step_times[step] = {user_id: first for user_id, first in entries}
    return step_times


def build_event_funnel(
    steps: list[str],
    *,
    start=None,
    end=None,
    include_anonymous: bool = DEFAULT_INCLUDE_ANONYMOUS,
    require_order: bool = DEFAULT_REQUIRE_ORDER,
) -> BaseServiceResult:
    if not steps:
        return BaseServiceResult.fail("Funnel steps are required")

    if len(set(steps)) != len(steps):
        return BaseServiceResult.fail("Funnel steps must be unique")

    warnings: list[str] = []
    known_steps = {choice[0] for choice in EventLog.EVENT_CHOICES}
    unknown_steps = [step for step in steps if step not in known_steps]
    if unknown_steps:
        warnings.append(UNKNOWN_STEP_WARNING)

    queryset = EventLog.objects.filter(event_type__in=steps)
    if start is not None:
        queryset = queryset.filter(created_at__gte=start)
    if end is not None:
        queryset = queryset.filter(created_at__lte=end)
    if not include_anonymous:
        queryset = queryset.filter(user_id__isnull=False)
    else:
        warnings.append(ANONYMOUS_GROUPED_WARNING)

    snapshots: list[FunnelStepSnapshot] = []
    previous_users: set[int | None] | None = None
    previous_times: dict[int | None, object] = {}
    previous_count = 0

    if require_order:
        step_times = _collect_step_times(steps, queryset)
        for step in steps:
            current_times = step_times.get(step, {})
            if previous_users is None:
                current_users = set(current_times.keys())
            else:
                current_users = {
                    user_id
                    for user_id in previous_users
                    if user_id in current_times
                    and current_times[user_id] >= previous_times[user_id]
                }
            current_count = len(current_users)
            conversion_rate = (
                PERCENT_MAX
                if previous_users is None and current_count > 0
                else _safe_percent(current_count, previous_count)
            )
            drop_off = max(previous_count - current_count, 0)
            drop_off_rate = _safe_percent(drop_off, previous_count)
            snapshots.append(
                FunnelStepSnapshot(
                    step=step,
                    user_count=current_count,
                    conversion_rate=conversion_rate,
                    drop_off=drop_off,
                    drop_off_rate=drop_off_rate,
                )
            )
            previous_users = current_users
            previous_times = {
                user_id: current_times[user_id] for user_id in current_users
            }
            previous_count = current_count
    else:
        step_users = _collect_step_users(steps, queryset)
        for step in steps:
            current_set = step_users.get(step, set())
            if previous_users is None:
                current_users = current_set
            else:
                current_users = current_set.intersection(previous_users)
            current_count = len(current_users)
            conversion_rate = (
                PERCENT_MAX
                if previous_users is None and current_count > 0
                else _safe_percent(current_count, previous_count)
            )
            drop_off = max(previous_count - current_count, 0)
            drop_off_rate = _safe_percent(drop_off, previous_count)
            snapshots.append(
                FunnelStepSnapshot(
                    step=step,
                    user_count=current_count,
                    conversion_rate=conversion_rate,
                    drop_off=drop_off,
                    drop_off_rate=drop_off_rate,
                )
            )
            previous_users = current_users
            previous_count = current_count

    total_users = snapshots[0].user_count if snapshots else 0
    last_step_users = snapshots[-1].user_count if snapshots else 0
    overall_conversion_rate = _safe_percent(last_step_users, total_users)

    summary = {
        "total_users": total_users,
        "last_step_users": last_step_users,
        "overall_conversion_rate": overall_conversion_rate,
        "start": start.isoformat() if start else None,
        "end": end.isoformat() if end else None,
        "include_anonymous": include_anonymous,
        "require_order": require_order,
    }

    meta = {"unknown_steps": unknown_steps} if unknown_steps else {}

    return BaseServiceResult.ok(
        data={"steps": steps, "snapshots": snapshots, "summary": summary},
        warnings=warnings,
        meta=meta,
    )
