from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable

from django.utils import timezone

from ..models import TestAttempt
from .code_similarity import similarity_score
from .service_result import BaseServiceResult

TEST_SIGNAL_FAST_INCORRECT = "fast_incorrect"
TEST_SIGNAL_RAPID_INCORRECTS = "rapid_incorrects"
CODE_SIGNAL_HIGH_SIMILARITY = "high_similarity"

CODE_FLAG_SIMILARITY = "code_similarity"

TEST_FAST_INCORRECT_MS = 1000
TEST_REPEAT_INCORRECT_MS = 2000
TEST_REPEAT_INCORRECT_THRESHOLD = 2
TEST_RECENT_WINDOW_HOURS = 1

CODE_SIMILARITY_THRESHOLD = 80.0

DEFAULT_TIME_TAKEN_MS = 0
MIN_TIME_TAKEN_MS = 1
MIN_RECENT_COUNT = 0
EMPTY_SIMILARITY_SCORE = None

ERROR_MISSING_TEST_CONTEXT = "User and test are required"
ERROR_SIMILARITY_FAILED = "Similarity check failed"


def _window_start(now: datetime) -> datetime:
    return now - timedelta(hours=TEST_RECENT_WINDOW_HOURS)


def _filter_recent_attempts(
    recent_attempts: Iterable[TestAttempt], start_at
) -> Iterable[TestAttempt]:
    if hasattr(recent_attempts, "filter"):
        return recent_attempts.filter(created_at__gte=start_at)
    return [attempt for attempt in recent_attempts if attempt.created_at >= start_at]


def _count_recent_incorrect(recent_attempts: Iterable[TestAttempt]) -> int:
    if hasattr(recent_attempts, "filter"):
        return recent_attempts.filter(is_correct=False).count()
    return sum(1 for attempt in recent_attempts if not attempt.is_correct)


def analyze_test_attempt(
    *,
    user,
    test,
    is_correct: bool,
    time_taken_ms: int,
    recent_attempts=None,
) -> BaseServiceResult:
    if user is None or test is None:
        return BaseServiceResult.fail(ERROR_MISSING_TEST_CONTEXT)

    now = timezone.now()
    time_taken_ms = int(time_taken_ms or DEFAULT_TIME_TAKEN_MS)
    start_at = _window_start(now)
    if recent_attempts is None:
        recent_attempts = TestAttempt.objects.filter(
            user=user, test=test, created_at__gte=start_at
        )
    else:
        recent_attempts = _filter_recent_attempts(recent_attempts, start_at)

    signals: list[str] = []
    recent_incorrect_count = MIN_RECENT_COUNT
    if not is_correct and time_taken_ms >= MIN_TIME_TAKEN_MS:
        if time_taken_ms < TEST_FAST_INCORRECT_MS:
            signals.append(TEST_SIGNAL_FAST_INCORRECT)
        if time_taken_ms < TEST_REPEAT_INCORRECT_MS:
            recent_incorrect_count = _count_recent_incorrect(recent_attempts)
            if recent_incorrect_count >= TEST_REPEAT_INCORRECT_THRESHOLD:
                signals.append(TEST_SIGNAL_RAPID_INCORRECTS)

    metadata = {
        "time_taken_ms": time_taken_ms,
        "recent_incorrect_attempts": recent_incorrect_count,
        "fast_incorrect_threshold_ms": TEST_FAST_INCORRECT_MS,
        "repeat_incorrect_threshold_ms": TEST_REPEAT_INCORRECT_MS,
        "repeat_incorrect_threshold": TEST_REPEAT_INCORRECT_THRESHOLD,
        "window_hours": TEST_RECENT_WINDOW_HOURS,
    }

    return BaseServiceResult.ok(
        data={
            "suspicious": bool(signals),
            "signals": signals,
            "metadata": metadata,
        }
    )


def analyze_code_submission(
    *,
    code: str,
    solution: str | None,
    threshold: float = CODE_SIMILARITY_THRESHOLD,
) -> BaseServiceResult:
    if not solution or not str(solution).strip():
        return BaseServiceResult.ok(
            data={
                "suspicious": False,
                "signals": [],
                "similarity_score": EMPTY_SIMILARITY_SCORE,
                "metadata": {"threshold": threshold},
            }
        )

    try:
        score = similarity_score(code or "", solution)
    except Exception:
        return BaseServiceResult.fail(ERROR_SIMILARITY_FAILED)

    signals: list[str] = []
    if score >= threshold:
        signals.append(CODE_SIGNAL_HIGH_SIMILARITY)

    return BaseServiceResult.ok(
        data={
            "suspicious": bool(signals),
            "signals": signals,
            "similarity_score": score,
            "metadata": {"similarity_score": score, "threshold": threshold},
        }
    )
