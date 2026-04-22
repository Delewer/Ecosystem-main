from __future__ import annotations

from datetime import datetime, time

from django.utils import timezone

from ..models import DailyChallenge, LessonProgress
from .service_result import BaseServiceResult


def get_todays_challenge(user) -> BaseServiceResult:
    """Return the active DailyChallenge for today, or fail if none exists."""
    today = timezone.localdate()
    challenge = (
        DailyChallenge.objects.filter(start_date__lte=today, end_date__gte=today)
        .select_related("lesson")
        .first()
    )
    if challenge is None:
        return BaseServiceResult.fail("No active challenge today.")

    completed = False
    if challenge.lesson_id:
        completed = LessonProgress.objects.filter(
            user=user,
            lesson=challenge.lesson,
            completed=True,
        ).exists()

    return BaseServiceResult.ok(
        data={
            "challenge": challenge,
            "completed": completed,
        }
    )


def get_challenge_time_remaining() -> int:
    """Return seconds until midnight (end of today's challenge window)."""
    now = timezone.localtime()
    midnight = datetime.combine(now.date(), time.max, tzinfo=now.tzinfo)
    remaining = (midnight - now).total_seconds()
    return max(0, int(remaining))


def has_user_completed_challenge(user, challenge: DailyChallenge) -> bool:
    """Check whether the user has completed the lesson tied to a challenge."""
    if not challenge.lesson_id:
        return False
    return LessonProgress.objects.filter(
        user=user,
        lesson=challenge.lesson,
        completed=True,
    ).exists()
