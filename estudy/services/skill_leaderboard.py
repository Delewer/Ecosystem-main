from __future__ import annotations

from django.db.models import Count, Sum, Value
from django.db.models.functions import Coalesce

from ..models import LessonProgress, LessonStreak, Skill, Subject
from .feature_flags import is_enabled as feature_enabled
from .service_result import BaseServiceResult

DEFAULT_LIMIT = 10
MAX_LIMIT = 100
MIN_LIMIT = 1

LIMIT_CLAMP_WARNING = "limit_clamped"
NO_ENTRIES_WARNING = "no_entries"

ERROR_MISSING_SKILL = "Skill is required"
ERROR_UNKNOWN_SKILL = "Skill not found"
ERROR_INVALID_LIMIT = "Limit must be a positive integer"

POINTS_DEFAULT = 0

ORDER_BY_FIELDS = ("-total_points", "-lessons_completed", "user__username")


def _normalize_limit(limit: int | None) -> tuple[int, list[str]]:
    if limit is None:
        return DEFAULT_LIMIT, []
    try:
        limit_value = int(limit)
    except (TypeError, ValueError):
        raise ValueError(ERROR_INVALID_LIMIT)
    if limit_value < MIN_LIMIT:
        raise ValueError(ERROR_INVALID_LIMIT)
    warnings = []
    if limit_value > MAX_LIMIT:
        limit_value = MAX_LIMIT
        warnings.append(LIMIT_CLAMP_WARNING)
    return limit_value, warnings


def _resolve_skill(*, skill_slug: str | None, skill_id: int | None) -> Skill | None:
    if skill_slug:
        return Skill.objects.filter(slug=skill_slug).first()
    if skill_id:
        return Skill.objects.filter(id=skill_id).first()
    return None


def build_skill_leaderboard(
    *,
    skill_slug: str | None = None,
    skill_id: int | None = None,
    limit: int | None = DEFAULT_LIMIT,
) -> BaseServiceResult:
    if not skill_slug and not skill_id:
        return BaseServiceResult.fail(ERROR_MISSING_SKILL)

    skill = _resolve_skill(skill_slug=skill_slug, skill_id=skill_id)
    if not skill:
        return BaseServiceResult.fail(ERROR_UNKNOWN_SKILL)

    try:
        limit_value, warnings = _normalize_limit(limit)
    except ValueError as exc:
        return BaseServiceResult.fail(str(exc))

    leaders = (
        LessonProgress.objects.filter(completed=True, lesson__skills=skill)
        .values("user_id", "user__username")
        .annotate(
            total_points=Coalesce(Sum("points_earned"), Value(POINTS_DEFAULT)),
            lessons_completed=Count("id"),
        )
        .order_by(*ORDER_BY_FIELDS)[:limit_value]
    )

    entries = [
        {
            "position": index + 1,
            "user_id": item["user_id"],
            "username": item["user__username"],
            "score": item["total_points"],
            "lessons_completed": item["lessons_completed"],
        }
        for index, item in enumerate(leaders)
    ]

    if not entries:
        warnings.append(NO_ENTRIES_WARNING)

    return BaseServiceResult.ok(
        data={
            "entries": entries,
            "row_count": len(entries),
            "skill": {
                "id": skill.id,
                "slug": skill.slug,
                "title": skill.title,
            },
            "limit": limit_value,
        },
        warnings=warnings,
    )


STREAK_LB_FEATURE_KEY = "streak_leaderboard_enabled"


def get_streak_leaderboard(
    subject: Subject,
    *,
    limit: int = 10,
    user=None,
) -> BaseServiceResult:
    """Return the top streak holders for a given subject.

    Gated behind the 'streak_leaderboard_enabled' feature flag.
    """
    if not feature_enabled(STREAK_LB_FEATURE_KEY, user=user):
        return BaseServiceResult.fail("Streak leaderboard is not enabled.")

    entries = (
        LessonStreak.objects.filter(subject=subject, current_streak__gt=0)
        .select_related("user")
        .order_by("-current_streak", "-longest_streak")[:limit]
    )

    result = [
        {
            "username": entry.user.username,
            "current_streak": entry.current_streak,
            "longest_streak": entry.longest_streak,
            "avatar_initial": entry.user.username[0].upper()
            if entry.user.username
            else "?",
        }
        for entry in entries
    ]

    return BaseServiceResult.ok(
        data={
            "entries": result,
            "subject_name": subject.name,
            "subject_slug": subject.slug,
        }
    )
