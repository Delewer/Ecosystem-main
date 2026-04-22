from __future__ import annotations

from datetime import datetime, time
from typing import Any

from django.db.models import Case, Count, IntegerField, Sum, When
from django.utils import timezone

from ..models import RobotLabLevelProgress, RobotLabRun


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        date_value = datetime.fromisoformat(value).date()
        return timezone.make_aware(datetime.combine(date_value, time.min))
    except Exception:
        return None


def build_robot_lab_analytics(*, filters: dict[str, Any]) -> dict[str, Any]:
    queryset = RobotLabRun.objects.select_related("user").all()

    level_id = str(filters.get("level_id") or "").strip()
    error_type = str(filters.get("error_type") or "").strip()
    date_from = _parse_date(str(filters.get("date_from") or "").strip())
    date_to = _parse_date(str(filters.get("date_to") or "").strip())
    classroom_id = str(filters.get("classroom") or "").strip()

    if level_id:
        queryset = queryset.filter(level_id=level_id)
    if error_type:
        queryset = queryset.filter(error_type=error_type)
    if date_from:
        queryset = queryset.filter(created_at__gte=date_from)
    if date_to:
        queryset = queryset.filter(created_at__lte=date_to + timezone.timedelta(days=1))

    if classroom_id:
        try:
            from ..models import ClassroomMembership

            user_ids = ClassroomMembership.objects.filter(
                classroom_id=int(classroom_id)
            ).values_list("user_id", flat=True)
            queryset = queryset.filter(user_id__in=list(user_ids))
        except Exception:
            queryset = queryset.none()

    total_runs = queryset.count()
    solved_runs = queryset.filter(solved=True).count()
    solve_rate = round((solved_runs / total_runs) * 100, 1) if total_runs else 0.0

    top_errors = list(
        queryset.exclude(primary_error="")
        .values("primary_error")
        .annotate(total=Count("id"))
        .order_by("-total")[:10]
    )

    per_level = list(
        queryset.values("level_id")
        .annotate(
            runs=Count("id"),
            solved_runs=Sum(
                Case(
                    When(solved__exact=True, then=1),
                    default=0,
                    output_field=IntegerField(),
                )
            ),
            failed_runs=Sum(
                Case(
                    When(solved__exact=False, then=1),
                    default=0,
                    output_field=IntegerField(),
                )
            ),
        )
        .order_by("level_id")
    )
    for row in per_level:
        runs = int(row["runs"] or 0)
        row["solved"] = int(row.pop("solved_runs") or 0)
        row["failed"] = int(row.pop("failed_runs") or 0)
        row["solve_rate"] = round((row["solved"] / runs) * 100, 1) if runs else 0.0

    recent_failed_runs = list(
        queryset.filter(solved=False)
        .order_by("-created_at")
        .values(
            "id",
            "level_id",
            "attempt_number",
            "error_type",
            "primary_error",
            "created_at",
            "execution_trace",
            "user__username",
        )[:20]
    )

    completion_stats = list(
        RobotLabLevelProgress.objects.values("level_id")
        .annotate(
            completed=Sum(
                Case(
                    When(completed__exact=True, then=1),
                    default=0,
                    output_field=IntegerField(),
                )
            ),
            users=Count("id"),
        )
        .order_by("level_id")
    )

    return {
        "summary": {
            "total_runs": total_runs,
            "solved_runs": solved_runs,
            "solve_rate": solve_rate,
        },
        "top_errors": top_errors,
        "per_level": per_level,
        "recent_failed_runs": recent_failed_runs,
        "completion_stats": completion_stats,
        "filters": {
            "level_id": level_id,
            "error_type": error_type,
            "date_from": filters.get("date_from"),
            "date_to": filters.get("date_to"),
            "classroom": classroom_id,
        },
    }
