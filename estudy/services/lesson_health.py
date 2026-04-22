from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from django.db.models import Q
from django.utils import timezone

from ..models import Lesson, LessonHealthScore
from .lesson_quality import LessonQualityAnalyzer
from .service_result import BaseServiceResult

QUALITY_MAX_SCORE = 5.0
PERCENT_MAX = 100.0
PERCENT_MIN = 0.0

WEIGHT_QUALITY = 0.5
WEIGHT_COMPLETION = 0.3
WEIGHT_RATING = 0.2
WEIGHT_SUM = WEIGHT_QUALITY + WEIGHT_COMPLETION + WEIGHT_RATING

SCORE_DECIMALS = 2
DETAILS_VERSION = "v1"


@dataclass(frozen=True)
class LessonHealthSnapshot:
    lesson_id: int
    score: float
    quality_score: float
    completion_rate: float
    avg_rating: float
    average_completion_time_minutes: float | None
    details: dict


def _clamp_percent(value: float) -> float:
    return max(PERCENT_MIN, min(PERCENT_MAX, value))


def _score_to_percent(score: float, max_score: float) -> float:
    if max_score <= 0:
        return PERCENT_MIN
    return _clamp_percent((score / max_score) * PERCENT_MAX)


def _health_score(
    quality_percent: float,
    completion_rate: float,
    rating_percent: float,
) -> float:
    weighted = (
        quality_percent * WEIGHT_QUALITY
        + completion_rate * WEIGHT_COMPLETION
        + rating_percent * WEIGHT_RATING
    )
    if WEIGHT_SUM <= 0:
        return PERCENT_MIN
    return round(_clamp_percent(weighted / WEIGHT_SUM), SCORE_DECIMALS)


def build_health_snapshot(lesson: Lesson) -> BaseServiceResult:
    quality = LessonQualityAnalyzer.get_lesson_quality_score(lesson)
    engagement = LessonQualityAnalyzer.get_lesson_engagement_metrics(lesson)
    avg_time = LessonQualityAnalyzer.get_average_completion_time(lesson)

    quality_score = float(quality.get("score") or 0.0)
    completion_rate = float(engagement.get("completion_rate") or 0.0)
    avg_rating = float(quality.get("overall_rating") or 0.0)

    quality_percent = _score_to_percent(quality_score, QUALITY_MAX_SCORE)
    rating_percent = _score_to_percent(avg_rating, QUALITY_MAX_SCORE)

    score = _health_score(quality_percent, completion_rate, rating_percent)

    warnings = []
    if quality.get("insufficient_data"):
        warnings.append("insufficient_quality_data")
    if engagement.get("total_views", 0) == 0:
        warnings.append("no_engagement_data")

    details = {
        "version": DETAILS_VERSION,
        "quality_percent": quality_percent,
        "rating_percent": rating_percent,
        "completion_rate": completion_rate,
        "weights": {
            "quality": WEIGHT_QUALITY,
            "completion": WEIGHT_COMPLETION,
            "rating": WEIGHT_RATING,
        },
    }

    snapshot = LessonHealthSnapshot(
        lesson_id=lesson.id,
        score=score,
        quality_score=quality_score,
        completion_rate=completion_rate,
        avg_rating=avg_rating,
        average_completion_time_minutes=avg_time,
        details=details,
    )
    return BaseServiceResult.ok(data={"snapshot": snapshot}, warnings=warnings)


def update_lesson_health_score(lesson: Lesson) -> BaseServiceResult:
    result = build_health_snapshot(lesson)
    snapshot = result.data["snapshot"]

    health, _ = LessonHealthScore.objects.update_or_create(
        lesson=lesson,
        defaults={
            "score": snapshot.score,
            "quality_score": snapshot.quality_score,
            "completion_rate": snapshot.completion_rate,
            "avg_rating": snapshot.avg_rating,
            "average_completion_time_minutes": snapshot.average_completion_time_minutes,
            "details": snapshot.details,
            "computed_at": timezone.now(),
        },
    )
    return BaseServiceResult.ok(
        data={
            "health": health,
            "snapshot": snapshot,
        },
        warnings=result.warnings,
    )


def refresh_all_lesson_health_scores(
    lessons: Iterable[Lesson] | None = None,
) -> BaseServiceResult:
    if lessons is None:
        lessons = Lesson.objects.filter(
            Q(progress_records__isnull=False) | Q(feedbacks__isnull=False)
        ).distinct()
    updated = 0
    for lesson in lessons:
        update_lesson_health_score(lesson)
        updated += 1
    return BaseServiceResult.ok(data={"updated": updated})
