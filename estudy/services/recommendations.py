from __future__ import annotations

from typing import List

from django.db.models import Count, Q

from ..models import Lesson, LessonProgress, LearningRecommendation


def calculate_recommendations(user, limit: int = 3) -> List[Lesson]:
    completed_ids = LessonProgress.objects.filter(user=user, completed=True).values_list("lesson_id", flat=True)
    queryset = (
        Lesson.objects.exclude(id__in=completed_ids)
        .order_by("date")
    )
    return list(queryset[:limit])


def refresh_recommendations(user, limit: int = 3) -> List[LearningRecommendation]:
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
