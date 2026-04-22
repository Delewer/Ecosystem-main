from __future__ import annotations

from typing import Dict

from django.utils import timezone

from ..models import EventLog, Test, TestAttempt
from ..services.gamification import record_lesson_completion
from .anti_cheat import analyze_test_attempt
from .audit_logger import log_event
from .mistake_explanations import build_test_mistake_explanation
from .socratic_followups import build_test_socratic_followups


def process_test_attempt(user, test: Test, answer: str, time_taken_ms: int = 0) -> Dict:
    """Process a test attempt: record attempt, compute correctness, points, bonus and
    mark lesson complete when correct.

    Returns a dict compatible with the JSON response used by the view.
    """
    now = timezone.now()
    one_hour_ago = now - timezone.timedelta(hours=1)
    recent_attempts = TestAttempt.objects.filter(
        user=user, test=test, created_at__gte=one_hour_ago
    ).order_by("-created_at")
    MAX_ATTEMPTS_PER_HOUR = 3
    COOLDOWN_SECONDS = 60
    if recent_attempts.count() >= MAX_ATTEMPTS_PER_HOUR:
        raise ValueError("Attempt limit reached. Try again later.")
    if recent_attempts.exists():
        delta = (now - recent_attempts.first().created_at).total_seconds()
        if delta < COOLDOWN_SECONDS:
            raise ValueError("Cooldown active. Please wait before retrying.")

    if test.time_limit_seconds and time_taken_ms:
        if time_taken_ms > test.time_limit_seconds * 1000:
            raise ValueError("Time limit exceeded.")

    is_correct = answer == test.correct_answer
    bonus = bool(
        is_correct
        and time_taken_ms
        and (time_taken_ms / 1000) <= test.bonus_time_threshold
    )
    awarded_points = test.points if is_correct else 0

    attempt, _ = TestAttempt.objects.update_or_create(
        test=test,
        user=user,
        defaults={
            "selected_answer": answer,
            "is_correct": is_correct,
            "time_taken_ms": time_taken_ms,
            "awarded_points": awarded_points,
            "earned_bonus": bonus,
            "feedback": test.explanation if not is_correct else "Grozaav!",
        },
    )

    suspicion_result = analyze_test_attempt(
        user=user,
        test=test,
        is_correct=is_correct,
        time_taken_ms=time_taken_ms,
        recent_attempts=recent_attempts,
    )
    if suspicion_result.success and suspicion_result.data.get("suspicious"):
        metadata = {
            "test_id": test.id,
            "attempt_id": attempt.id,
            "suspicious": True,
            "signals": suspicion_result.data.get("signals", []),
        }
        metadata.update(suspicion_result.data.get("metadata", {}))
        log_event(
            EventLog.EVENT_TEST_START,
            user=user,
            metadata=metadata,
        )

    response: Dict = {
        "is_correct": is_correct,
        "correct_answer": test.correct_answer,
        "explanation": test.explanation,
        "awarded_points": attempt.awarded_points,
        "earned_bonus": bonus,
    }

    if is_correct:
        # mark lesson completed (convert ms to seconds for record_lesson_completion)
        seconds = time_taken_ms // 1000 if time_taken_ms else None
        progress_snapshot = record_lesson_completion(
            user, test.lesson, seconds_spent=seconds
        )
        response.update(
            {
                "lesson_completed": True,
                "progress_percent": progress_snapshot["percent"],
                "completed_count": progress_snapshot["completed"],
                "total_lessons": progress_snapshot["total"],
            }
        )
    else:
        response["lesson_completed"] = False
        explanation_result = build_test_mistake_explanation(
            test, selected_answer=answer
        )
        if explanation_result.success:
            response["mistake_explanation"] = explanation_result.data.get("explanation")
        followup_result = build_test_socratic_followups(test, selected_answer=answer)
        if followup_result.success:
            response["socratic_questions"] = followup_result.data.get("questions", [])

    return response
