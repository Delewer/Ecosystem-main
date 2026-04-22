from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from django.contrib.auth import get_user_model
from django.db.models import Min
from django.utils import timezone

from ..models import EventLog, LessonProgress, TestAttempt
from .service_result import BaseServiceResult

PERIOD_WEEKLY = "weekly"
PERIOD_MONTHLY = "monthly"
SUPPORTED_PERIODS = {PERIOD_WEEKLY, PERIOD_MONTHLY}

ACTIVITY_SOURCE_LESSON_PROGRESS = "lesson_progress"
ACTIVITY_SOURCE_TEST_ATTEMPT = "test_attempt"
ACTIVITY_SOURCE_EVENT_LOG = "event_log"
SUPPORTED_ACTIVITY_SOURCES = {
    ACTIVITY_SOURCE_LESSON_PROGRESS,
    ACTIVITY_SOURCE_TEST_ATTEMPT,
    ACTIVITY_SOURCE_EVENT_LOG,
}

PERCENT_MIN = 0.0
PERCENT_MAX = 100.0
SCORE_DECIMALS = 2

NEXT_DAY_OFFSET = 1
DAYS_PER_WEEK = 7
WEEK_START_DAY = 0
MONTH_START_DAY = 1
NEXT_PERIOD_OFFSET = 1

MIN_PERIODS = 0

NO_USERS_WARNING = "no_users"
NO_COHORTS_WARNING = "no_cohorts"
NO_ACTIVITY_WARNING = "no_activity"


@dataclass(frozen=True)
class CohortPeriodSnapshot:
    period_index: int
    active_users: int
    retention_rate: float


@dataclass(frozen=True)
class CohortSnapshot:
    cohort_start: date
    cohort_size: int
    periods: list[CohortPeriodSnapshot]


def _as_date(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    return value


def _start_of_week(value: date) -> date:
    return value - timedelta(days=value.weekday() - WEEK_START_DAY)


def _start_of_month(value: date) -> date:
    return value.replace(day=MONTH_START_DAY)


def _add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, MONTH_START_DAY)


def _add_period(value: date, period: str, count: int) -> date:
    if period == PERIOD_WEEKLY:
        return value + timedelta(days=count * DAYS_PER_WEEK)
    return _add_months(value, count)


def _period_index(start: date, current: date, period: str) -> int:
    if current < start:
        return -1
    if period == PERIOD_WEEKLY:
        delta_days = (current - start).days
        return delta_days // DAYS_PER_WEEK
    month_delta = (current.year - start.year) * 12 + (current.month - start.month)
    return month_delta


def _align_start(value: date, period: str) -> date:
    if period == PERIOD_WEEKLY:
        return _start_of_week(value)
    return _start_of_month(value)


def _iter_period_starts(start: date, end: date, period: str) -> list[date]:
    current = _align_start(start, period)
    starts = []
    while current <= end:
        starts.append(current)
        current = _add_period(current, period, NEXT_PERIOD_OFFSET)
    return starts


def _safe_percent(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return PERCENT_MIN
    return round((numerator / denominator) * PERCENT_MAX, SCORE_DECIMALS)


def _activity_queryset(source: str):
    if source == ACTIVITY_SOURCE_LESSON_PROGRESS:
        return LessonProgress.objects.all(), "updated_at"
    if source == ACTIVITY_SOURCE_TEST_ATTEMPT:
        return TestAttempt.objects.all(), "created_at"
    if source == ACTIVITY_SOURCE_EVENT_LOG:
        return EventLog.objects.all(), "created_at"
    return None, ""


def build_user_cohort_retention(
    *,
    start=None,
    end=None,
    period: str = PERIOD_WEEKLY,
    max_periods: int | None = None,
    activity_source: str = ACTIVITY_SOURCE_LESSON_PROGRESS,
    event_types: list[str] | None = None,
) -> BaseServiceResult:
    if period not in SUPPORTED_PERIODS:
        return BaseServiceResult.fail("Unsupported cohort period")
    if activity_source not in SUPPORTED_ACTIVITY_SOURCES:
        return BaseServiceResult.fail("Unsupported activity source")

    User = get_user_model()
    earliest_join = User.objects.aggregate(first=Min("date_joined")).get("first")
    if earliest_join is None:
        return BaseServiceResult.ok(
            data={"cohorts": [], "summary": {"cohort_count": 0}},
            warnings=[NO_USERS_WARNING],
        )

    start_date = _as_date(start) or earliest_join.date()
    end_date = _as_date(end) or timezone.localdate()
    if start_date > end_date:
        return BaseServiceResult.fail("Start date must be before end date")

    period_starts = _iter_period_starts(start_date, end_date, period)
    if not period_starts:
        return BaseServiceResult.ok(
            data={"cohorts": [], "summary": {"cohort_count": 0}},
            warnings=[NO_COHORTS_WARNING],
        )

    users = User.objects.filter(
        date_joined__date__gte=start_date, date_joined__date__lte=end_date
    ).values_list("id", "date_joined")
    user_to_cohort: dict[int, date] = {}
    cohort_users: dict[date, set[int]] = {}
    for user_id, joined_at in users:
        joined_date = joined_at.date()
        cohort_start = _align_start(joined_date, period)
        user_to_cohort[user_id] = cohort_start
        cohort_users.setdefault(cohort_start, set()).add(user_id)

    cohort_starts = sorted(cohort_users.keys())
    if not cohort_starts:
        return BaseServiceResult.ok(
            data={"cohorts": [], "summary": {"cohort_count": 0}},
            warnings=[NO_COHORTS_WARNING],
        )

    last_cohort_start = cohort_starts[-1]
    max_period_index = max_periods
    if max_period_index is None:
        max_period_index = _period_index(
            last_cohort_start, timezone.localdate(), period
        )
    if max_period_index < MIN_PERIODS:
        return BaseServiceResult.fail("Max periods must be non-negative")

    analysis_end = _add_period(
        last_cohort_start, period, max_period_index + NEXT_PERIOD_OFFSET
    )
    analysis_cap = timezone.localdate() + timedelta(days=NEXT_DAY_OFFSET)
    if analysis_end > analysis_cap:
        analysis_end = analysis_cap

    activity_qs, date_field = _activity_queryset(activity_source)
    if activity_qs is None:
        return BaseServiceResult.fail("Unsupported activity source")

    activity_qs = activity_qs.filter(user_id__in=user_to_cohort.keys())
    if activity_source == ACTIVITY_SOURCE_EVENT_LOG and event_types:
        activity_qs = activity_qs.filter(event_type__in=event_types)

    activity_qs = activity_qs.filter(
        **{
            f"{date_field}__date__gte": period_starts[0],
            f"{date_field}__date__lt": analysis_end,
        }
    )

    activity_map: dict[date, dict[int, set[int]]] = {}
    for user_id, activity_dt in activity_qs.values_list("user_id", date_field):
        cohort_start = user_to_cohort.get(user_id)
        if cohort_start is None:
            continue
        activity_date = activity_dt.date()
        index = _period_index(cohort_start, activity_date, period)
        if index < MIN_PERIODS or index > max_period_index:
            continue
        activity_map.setdefault(cohort_start, {}).setdefault(index, set()).add(user_id)

    snapshots: list[CohortSnapshot] = []
    for cohort_start in cohort_starts:
        users_in_cohort = cohort_users.get(cohort_start, set())
        cohort_size = len(users_in_cohort)
        periods: list[CohortPeriodSnapshot] = []
        for index in range(max_period_index + NEXT_PERIOD_OFFSET):
            active_set = activity_map.get(cohort_start, {}).get(index, set())
            active_count = len(active_set)
            periods.append(
                CohortPeriodSnapshot(
                    period_index=index,
                    active_users=active_count,
                    retention_rate=_safe_percent(active_count, cohort_size),
                )
            )
        snapshots.append(
            CohortSnapshot(
                cohort_start=cohort_start,
                cohort_size=cohort_size,
                periods=periods,
            )
        )

    warnings = []
    if not activity_map:
        warnings.append(NO_ACTIVITY_WARNING)

    summary = {
        "cohort_count": len(snapshots),
        "cohort_user_count": sum(item.cohort_size for item in snapshots),
        "period": period,
        "max_periods": max_period_index,
        "start": start_date.isoformat(),
        "end": end_date.isoformat(),
        "activity_source": activity_source,
    }

    return BaseServiceResult.ok(
        data={"cohorts": snapshots, "summary": summary},
        warnings=warnings,
    )
