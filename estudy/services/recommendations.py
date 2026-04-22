from __future__ import annotations

from typing import List

from django.core.cache import cache

from ..models import LearningRecommendation, Lesson, LessonProgress


def calculate_recommendations(user, limit: int = 3) -> List[Lesson]:
    """Return recommended Lesson objects for a user, cached per user for 5 minutes."""
    cache_key = f"estudy:recs:{user.id}:{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    completed_ids = LessonProgress.objects.filter(
        user=user, completed=True
    ).values_list("lesson_id", flat=True)
    queryset = Lesson.objects.exclude(id__in=completed_ids).order_by("date")
    result = list(queryset[:limit])
    cache.set(cache_key, result, 60 * 5)
    return result


def refresh_recommendations(user, limit: int = 3) -> List[LearningRecommendation]:
    # invalidate cache then recalc
    cache_key = f"estudy:recs:{user.id}:{limit}"
    cache.delete(cache_key)
    lessons = calculate_recommendations(user, limit=limit)
    LearningRecommendation.objects.filter(user=user).delete()
    recommendations = []
    for index, lesson in enumerate(lessons):
        recommendation = LearningRecommendation.objects.create(
            user=user,
            lesson=lesson,
            reason="Bine de parcurs in continuare",
            score=1.0 - (index * 0.1),
        )
        recommendations.append(recommendation)
    return recommendations
