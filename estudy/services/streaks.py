from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

from ..models import LessonProgress, UserProfile
from .service_result import BaseServiceResult


def update_streak_on_completion(user) -> BaseServiceResult:
    """Recalculate current_streak and longest_streak after a lesson completion.

    A streak day counts when the user has at least one lesson completed on that
    calendar date.  Consecutive calendar days (going backwards from today) form
    the current streak.
    """
    profile: UserProfile = user.userprofile
    today = timezone.localdate()

    completed_dates = (
        LessonProgress.objects.filter(
            user=user, completed=True, completed_at__isnull=False
        )
        .values_list("completed_at", flat=True)
        .order_by("-completed_at")
    )

    unique_dates = sorted({d.date() for d in completed_dates}, reverse=True)

    if not unique_dates or unique_dates[0] != today:
        profile.current_streak = 0
        profile.save(update_fields=["current_streak"])
        return BaseServiceResult.ok(
            data={"current_streak": 0, "longest_streak": profile.longest_streak}
        )

    streak = 1
    for i in range(1, len(unique_dates)):
        if unique_dates[i] == today - timedelta(days=i):
            streak += 1
        else:
            break

    profile.current_streak = streak
    if streak > profile.longest_streak:
        profile.longest_streak = streak
    profile.save(update_fields=["current_streak", "longest_streak"])
    return BaseServiceResult.ok(
        data={"current_streak": streak, "longest_streak": profile.longest_streak}
    )
