from __future__ import annotations

from dataclasses import dataclass

from ..models import CodeExercise, CodeSubmission, Lesson, Test, TestAttempt
from .assessment_enhanced import generate_personalized_practice_plan
from .service_result import BaseServiceResult

DEFAULT_DAYS = 7
DEFAULT_TASKS_PER_DAY = 2
MIN_TASKS_PER_DAY = 1
MAX_TASKS_PER_DAY = 3

DEFAULT_TEST_LIMIT = 3

TASK_LESSON_REVIEW = "lesson_review"
TASK_QUIZ_RETRY = "quiz_retry"
TASK_CODE_EXERCISE = "code_exercise"

REASON_REVIEW = "Review the lesson content to reinforce the key idea."
REASON_FAILED_QUESTIONS = "Retry questions you recently missed."
REASON_PRACTICE_QUIZ = "Quick quiz to reinforce the concept."
REASON_CODE_PRACTICE = "Apply the concept in code."

WARNING_NO_PLAN_ITEMS = "no_plan_items"


@dataclass(frozen=True)
class PracticeTask:
    task_type: str
    lesson_id: int
    lesson_title: str
    reason: str
    estimated_time: int
    items: list[int]


def _unique_ids(values: list[int]) -> list[int]:
    seen = set()
    result = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _lesson_review_task(plan_item: dict) -> PracticeTask:
    lesson = plan_item["lesson"]
    return PracticeTask(
        task_type=TASK_LESSON_REVIEW,
        lesson_id=lesson.id,
        lesson_title=lesson.title,
        reason=plan_item.get("reason") or REASON_REVIEW,
        estimated_time=lesson.duration_minutes,
        items=[],
    )


def _quiz_retry_task(
    user,
    lesson: Lesson,
    *,
    test_limit: int,
) -> PracticeTask | None:
    failed_ids = list(
        TestAttempt.objects.filter(user=user, test__lesson=lesson, is_correct=False)
        .order_by("-created_at")
        .values_list("test_id", flat=True)
    )
    if failed_ids:
        test_ids = _unique_ids(failed_ids)[:test_limit]
        reason = REASON_FAILED_QUESTIONS
    else:
        test_ids = list(
            Test.objects.filter(lesson=lesson)
            .order_by("id")
            .values_list("id", flat=True)[:test_limit]
        )
        reason = REASON_PRACTICE_QUIZ

    if not test_ids:
        return None

    return PracticeTask(
        task_type=TASK_QUIZ_RETRY,
        lesson_id=lesson.id,
        lesson_title=lesson.title,
        reason=reason,
        estimated_time=lesson.duration_minutes,
        items=test_ids,
    )


def _code_exercise_task(
    user,
    lesson: Lesson,
) -> PracticeTask | None:
    exercises = CodeExercise.objects.filter(lesson=lesson).order_by("order", "id")
    if not exercises.exists():
        return None

    solved_ids = set(
        CodeSubmission.objects.filter(
            user=user, exercise__lesson=lesson, is_correct=True
        ).values_list("exercise_id", flat=True)
    )
    exercise = exercises.exclude(id__in=solved_ids).first() or exercises.first()
    if exercise is None:
        return None

    return PracticeTask(
        task_type=TASK_CODE_EXERCISE,
        lesson_id=lesson.id,
        lesson_title=lesson.title,
        reason=REASON_CODE_PRACTICE,
        estimated_time=lesson.duration_minutes,
        items=[exercise.id],
    )


def _normalize_tasks_per_day(value: int) -> int:
    if value < MIN_TASKS_PER_DAY:
        return MIN_TASKS_PER_DAY
    return min(value, MAX_TASKS_PER_DAY)


def generate_personalized_practice(
    user,
    *,
    days: int = DEFAULT_DAYS,
    tasks_per_day: int = DEFAULT_TASKS_PER_DAY,
    test_limit: int = DEFAULT_TEST_LIMIT,
) -> BaseServiceResult:
    if tasks_per_day < MIN_TASKS_PER_DAY:
        return BaseServiceResult.fail("Tasks per day must be positive")

    tasks_per_day = _normalize_tasks_per_day(tasks_per_day)
    plan_items = generate_personalized_practice_plan(user, days=days)

    if not plan_items:
        return BaseServiceResult.ok(
            data={"days": [], "summary": {"total_days": 0, "total_tasks": 0}},
            warnings=[WARNING_NO_PLAN_ITEMS],
        )

    days_payload = []
    total_tasks = 0
    for plan_item in plan_items:
        lesson = plan_item["lesson"]
        tasks: list[PracticeTask] = [_lesson_review_task(plan_item)]

        if len(tasks) < tasks_per_day:
            quiz_task = _quiz_retry_task(user, lesson, test_limit=test_limit)
            if quiz_task:
                tasks.append(quiz_task)

        if len(tasks) < tasks_per_day:
            code_task = _code_exercise_task(user, lesson)
            if code_task:
                tasks.append(code_task)

        tasks = tasks[:tasks_per_day]
        total_tasks += len(tasks)

        days_payload.append(
            {
                "day": plan_item.get("day"),
                "lesson_id": lesson.id,
                "lesson_title": lesson.title,
                "priority": plan_item.get("priority"),
                "tasks": [task.__dict__ for task in tasks],
            }
        )

    summary = {
        "total_days": len(days_payload),
        "total_tasks": total_tasks,
        "tasks_per_day": tasks_per_day,
    }

    return BaseServiceResult.ok(data={"days": days_payload, "summary": summary})
