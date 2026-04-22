from __future__ import annotations

from dataclasses import dataclass

from django.db.models import Avg

from ..models import Lesson, TestAttempt
from .service_result import BaseServiceResult

PERCENT_MIN = 0.0
PERCENT_MAX = 100.0
SCORE_DECIMALS = 1

SUCCESS_RATE_EASY_THRESHOLD = 80.0
SUCCESS_RATE_MEDIUM_THRESHOLD = 50.0

MS_PER_SECOND = 1000.0

RECOMMEND_MATCH = "difficulty_match"
RECOMMEND_LOWER = "lower_difficulty"
RECOMMEND_HIGHER = "raise_difficulty"

INSUFFICIENT_DATA_WARNING = "insufficient_data"
UNKNOWN_RESULT_WARNING = "unknown_result"

DEFAULT_MAX_MISMATCHES = 100
MIN_MAX_MISMATCHES = 0


@dataclass(frozen=True)
class DifficultyMismatchSnapshot:
    lesson_id: int
    declared_difficulty: str
    real_difficulty: str
    difficulty_match: bool
    success_rate: float
    avg_time_seconds: float
    total_attempts: int
    recommendation: str


def _clamp_percent(value: float) -> float:
    return max(PERCENT_MIN, min(PERCENT_MAX, value))


def _classify_real_difficulty(success_rate: float) -> str:
    if success_rate >= SUCCESS_RATE_EASY_THRESHOLD:
        return Lesson.DIFFICULTY_BEGINNER
    if success_rate >= SUCCESS_RATE_MEDIUM_THRESHOLD:
        return Lesson.DIFFICULTY_INTERMEDIATE
    return Lesson.DIFFICULTY_ADVANCED


def _difficulty_rank(value: str) -> int:
    mapping = {
        Lesson.DIFFICULTY_BEGINNER: 1,
        Lesson.DIFFICULTY_INTERMEDIATE: 2,
        Lesson.DIFFICULTY_ADVANCED: 3,
    }
    return mapping.get(value, 0)


def _recommendation(declared: str, real: str) -> str:
    if declared == real:
        return RECOMMEND_MATCH
    if _difficulty_rank(real) > _difficulty_rank(declared):
        return RECOMMEND_HIGHER
    return RECOMMEND_LOWER


def build_lesson_difficulty_analysis(lesson: Lesson) -> BaseServiceResult:
    attempts = TestAttempt.objects.filter(test__lesson=lesson)
    total = attempts.count()
    if total == 0:
        return BaseServiceResult.ok(
            data={"analysis": {"lesson": lesson.title, "insufficient_data": True}},
            warnings=[INSUFFICIENT_DATA_WARNING],
        )

    correct = attempts.filter(is_correct=True).count()
    success_rate = _clamp_percent((correct / total) * PERCENT_MAX)

    avg_time_ms = attempts.aggregate(avg=Avg("time_taken_ms")).get("avg") or 0
    avg_time_seconds = round(avg_time_ms / MS_PER_SECOND, SCORE_DECIMALS)

    real_difficulty = _classify_real_difficulty(success_rate)
    declared_difficulty = lesson.difficulty
    difficulty_match = real_difficulty == declared_difficulty
    recommendation = _recommendation(declared_difficulty, real_difficulty)

    snapshot = DifficultyMismatchSnapshot(
        lesson_id=lesson.id,
        declared_difficulty=declared_difficulty,
        real_difficulty=real_difficulty,
        difficulty_match=difficulty_match,
        success_rate=round(success_rate, SCORE_DECIMALS),
        avg_time_seconds=avg_time_seconds,
        total_attempts=total,
        recommendation=recommendation,
    )

    analysis = {
        "lesson": lesson.title,
        "declared_difficulty": snapshot.declared_difficulty,
        "real_difficulty": snapshot.real_difficulty,
        "difficulty_match": snapshot.difficulty_match,
        "success_rate": snapshot.success_rate,
        "avg_time_seconds": snapshot.avg_time_seconds,
        "total_attempts": snapshot.total_attempts,
        "recommendation": snapshot.recommendation,
    }

    return BaseServiceResult.ok(data={"analysis": analysis, "snapshot": snapshot})


def find_difficulty_mismatches(
    lessons=None, *, max_results: int = DEFAULT_MAX_MISMATCHES
) -> BaseServiceResult:
    if max_results < MIN_MAX_MISMATCHES:
        return BaseServiceResult.fail("Max results must be non-negative")

    if lessons is None:
        lessons = Lesson.objects.filter(tests__attempts__isnull=False).distinct()

    mismatches: list[dict] = []
    insufficient = 0
    checked = 0
    warnings: set[str] = set()

    for lesson in lessons:
        checked += 1
        result = build_lesson_difficulty_analysis(lesson)
        warnings.update(result.warnings)
        if not result.success:
            warnings.add(UNKNOWN_RESULT_WARNING)
            continue
        analysis = result.data.get("analysis", {})
        if analysis.get("insufficient_data"):
            insufficient += 1
            continue
        if not analysis.get("difficulty_match", False):
            mismatches.append(analysis)
            if max_results > MIN_MAX_MISMATCHES and len(mismatches) >= max_results:
                break

    return BaseServiceResult.ok(
        data={
            "mismatches": mismatches,
            "checked": checked,
            "insufficient": insufficient,
        },
        warnings=sorted(warnings),
    )
