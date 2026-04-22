"""
Learning path and diagnostic utilities.

Rules:
- keep views thin, call these helpers instead
- keep logic small and testable
"""

from datetime import timedelta
from typing import Iterable, List, Optional

from django.utils import timezone

from ..models import (
    Course,
    DiagnosticAttempt,
    DiagnosticTest,
    LearningPlan,
    LearningPlanItem,
    Lesson,
    TestAttempt,
    TopicTag,
)


def _normalize_plan_type(days: int) -> str:
    if days <= 7:
        return LearningPlan.PLAN_7_DAYS
    if days <= 14:
        return LearningPlan.PLAN_14_DAYS
    return LearningPlan.PLAN_30_DAYS


def build_learning_path(
    user, course: Optional[Course] = None, days: int = 14
) -> LearningPlan:
    """
    Create a learning plan and distribute lessons over a simple schedule.
    """
    plan = LearningPlan.objects.create(
        user=user,
        course=course,
        plan_type=_normalize_plan_type(days),
        start_date=timezone.now().date(),
    )

    lessons = Lesson.objects.all().select_related("module", "subject")
    if course:
        lessons = lessons.filter(module__course=course)
    lessons = lessons.order_by("module__order", "date", "id")

    if not lessons.exists():
        return plan

    due_date = plan.start_date
    for index, lesson in enumerate(lessons):
        if index and index % max(1, len(lessons) // max(days, 1)) == 0:
            due_date += timedelta(days=1)
        LearningPlanItem.objects.create(
            plan=plan,
            lesson=lesson,
            order=index + 1,
            due_date=due_date,
        )
    return plan


def run_entry_diagnostic(
    user, diagnostic_test: DiagnosticTest, score: int
) -> DiagnosticAttempt:
    """
    Store a diagnostic attempt and return the recommendation snapshot.
    """
    recommendation_level = diagnostic_test.recommended_level
    return DiagnosticAttempt.objects.update_or_create(
        test=diagnostic_test,
        user=user,
        defaults={
            "score": score,
            "recommended_course": diagnostic_test.course,
            "recommended_module": diagnostic_test.module,
            "recommended_level": recommendation_level,
            "notes": "Auto-created recommendation from entry diagnostic",
        },
    )[0]


def detect_weak_topics(user, *, min_attempts: int = 2) -> List[dict]:
    """
    Identify weak topics based on test attempts.
    """
    topic_stats: dict[int, dict] = {}
    attempts = (
        TestAttempt.objects.filter(user=user)
        .select_related("test__lesson")
        .prefetch_related("test__lesson__topics")
    )
    for attempt in attempts:
        lesson_topics: Iterable[TopicTag] = attempt.test.lesson.topics.all()
        for topic in lesson_topics:
            data = topic_stats.setdefault(
                topic.id,
                {"topic": topic, "correct": 0, "total": 0},
            )
            data["total"] += 1
            if attempt.is_correct:
                data["correct"] += 1

    weak = []
    for data in topic_stats.values():
        if data["total"] < min_attempts:
            continue
        rate = (data["correct"] / data["total"]) * 100
        if rate < 70:
            weak.append(
                {
                    "topic": data["topic"],
                    "success_rate": rate,
                    "attempts": data["total"],
                }
            )
    weak.sort(key=lambda item: item["success_rate"])
    return weak


def generate_micro_remediation_tasks(
    weak_topics: List[dict], *, per_topic: int = 3
) -> List[str]:
    """
    Generate small remediation ideas for weak topics.
    """
    tasks: List[str] = []
    for entry in weak_topics:
        topic_name = entry["topic"].name
        tasks.append(f"Review summary notes for topic '{topic_name}'.")
        if per_topic > 1:
            tasks.append(f"Re-attempt a quiz question for '{topic_name}'.")
        if per_topic > 2:
            tasks.append(f"Pair up with a peer to explain '{topic_name}' in 5 minutes.")
        if len(tasks) >= per_topic * len(weak_topics):
            break
    return tasks
