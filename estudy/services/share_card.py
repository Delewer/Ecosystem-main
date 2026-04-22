from __future__ import annotations

from ..models import Lesson, LessonProgress
from .service_result import BaseServiceResult


def build_share_card_context(user, lesson: Lesson) -> BaseServiceResult:
    """Build context for the shareable victory card after lesson completion."""
    progress = (
        LessonProgress.objects.filter(user=user, lesson=lesson, completed=True)
        .select_related("lesson")
        .first()
    )

    if not progress:
        return BaseServiceResult.fail("Lesson not completed by this user.")

    profile = user.userprofile
    return BaseServiceResult.ok(
        data={
            "lesson_title": lesson.title,
            "xp_earned": progress.points_earned or lesson.xp_reward,
            "username": profile.display_or_username(),
            "level": profile.level,
            "current_streak": profile.current_streak,
        }
    )
