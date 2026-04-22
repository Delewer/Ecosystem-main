from __future__ import annotations

from typing import Dict

from ..models import Lesson, LessonProgress
from .gamification import (
    build_overall_progress,
    invalidate_overall_progress_cache,
    record_lesson_completion,
)


def toggle_lesson_completion_service(
    user, lesson: Lesson, seconds_spent: int | None = None
) -> Dict:
    """Toggle completion for a user+lesson.

    Returns a dict with keys:
      - completed: bool (new state)
      - progress_snapshot: dict (same shape as build_overall_progress)

    This delegates to existing model/service helpers so behavior remains consistent
    with the rest of the codebase (XP awarding, missions, badges).
    """
    progress, _ = LessonProgress.objects.get_or_create(user=user, lesson=lesson)
    if progress.completed:
        # unmark
        progress.completed = False
        progress.completed_at = None
        progress.save(update_fields=["completed", "completed_at", "updated_at"])
        invalidate_overall_progress_cache(user)
        snapshot = build_overall_progress(user)
        return {"completed": False, "progress_snapshot": snapshot}

    # mark completed (this handles XP, badges, missions)
    snapshot = record_lesson_completion(user, lesson, seconds_spent=seconds_spent)
    return {"completed": True, "progress_snapshot": snapshot}
