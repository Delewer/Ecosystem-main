"""
High-level analytics summaries for students, teachers, and product metrics.
"""

from datetime import timedelta
from typing import Dict, List, Set

from django.db.models import Avg
from django.utils import timezone

from ..models import LessonAnalytics, LessonProgress, TestAttempt
from .analytics import LessonAnalyticsService

try:
    from ..models import Classroom, ClassroomMembership
except Exception:  # pragma: no cover - optional feature
    Classroom = None
    ClassroomMembership = None


def _topic_mastery(user) -> List[dict]:
    """Compute per-topic success rates from test attempts."""
    stats: Dict[int, Dict[str, float]] = {}
    attempts = (
        TestAttempt.objects.filter(user=user)
        .select_related("test__lesson")
        .prefetch_related("test__lesson__topics")
    )
    for attempt in attempts:
        for topic in attempt.test.lesson.topics.all():
            entry = stats.setdefault(
                topic.id, {"topic": topic, "correct": 0, "total": 0}
            )
            entry["total"] += 1
            if attempt.is_correct:
                entry["correct"] += 1
    mastery: List[dict] = []
    for entry in stats.values():
        if entry["total"] == 0:
            continue
        rate = (entry["correct"] / entry["total"]) * 100
        mastery.append(
            {
                "topic": entry["topic"],
                "success_rate": rate,
                "attempts": entry["total"],
            }
        )
    mastery.sort(key=lambda item: item["success_rate"])
    return mastery


def get_student_analytics(user) -> dict:
    """Return student-level analytics snapshot."""
    progress_qs = LessonProgress.objects.filter(user=user)
    completed_qs = progress_qs.filter(completed=True)
    completed_count = completed_qs.count()
    progress_lesson_ids = set(progress_qs.values_list("lesson_id", flat=True))
    attempt_lesson_ids = set(
        TestAttempt.objects.filter(user=user).values_list("test__lesson_id", flat=True)
    )
    engaged_lesson_ids = progress_lesson_ids.union(attempt_lesson_ids)
    total_lessons = len(engaged_lesson_ids)
    completion_rate = (completed_count / total_lessons * 100) if total_lessons else 0

    avg_speed = (
        completed_qs.aggregate(avg=Avg("fastest_completion_seconds"))["avg"] or 0
    )
    streak = getattr(getattr(user, "userprofile", None), "streak", 0)

    attempts = TestAttempt.objects.filter(user=user)
    avg_score = attempts.aggregate(avg=Avg("awarded_points"))["avg"] or 0

    mastery = _topic_mastery(user)

    return {
        "completion_rate": completion_rate,
        "completed_lessons": completed_count,
        "total_lessons": total_lessons,
        "avg_speed_seconds": avg_speed,
        "streak_days": streak,
        "avg_score": avg_score,
        "topic_mastery": mastery,
    }


def detect_student_risk(user) -> dict:
    """Simple risk detection based on low completion and scores."""
    metrics = get_student_analytics(user)
    risks: List[str] = []
    if metrics["completion_rate"] < 50:
        risks.append("Low completion rate")
    if metrics["avg_score"] < 60:
        risks.append("Low test scores")
    if metrics["streak_days"] <= 0:
        risks.append("No activity streak")
    return {
        "at_risk": bool(risks),
        "reasons": risks,
        "snapshot": metrics,
    }


def get_teacher_class_overview(classroom=None) -> dict:
    """Class or global overview for teachers."""
    if Classroom is None:
        # Fallback to global aggregates
        lesson_stats = LessonAnalyticsService.get_lesson_overview_stats(None)
        return {"type": "global", "lesson_stats": lesson_stats, "students": 0}

    members: Set[int] = set()
    if classroom and ClassroomMembership:
        members = set(
            ClassroomMembership.objects.filter(classroom=classroom).values_list(
                "user_id", flat=True
            )
        )
    progress_qs = LessonProgress.objects.all()
    if members:
        progress_qs = progress_qs.filter(user_id__in=members)

    completion_rate = (
        progress_qs.filter(completed=True).count() / progress_qs.count() * 100
        if progress_qs.exists()
        else 0
    )
    lesson_difficulty = LessonAnalytics.objects.aggregate(
        avg_score=Avg("avg_score"), avg_completion_rate=Avg("completion_rate")
    )
    return {
        "type": "classroom" if classroom else "global",
        "student_count": len(members) if members else 0,
        "completion_rate": completion_rate,
        "lesson_difficulty": lesson_difficulty,
    }


def get_product_metrics() -> dict:
    """Product analytics: DAU/MAU, retention, session time."""
    now = timezone.now()
    day_cutoff = now - timedelta(days=1)
    week_cutoff = now - timedelta(days=7)
    month_cutoff = now - timedelta(days=30)

    daily_users = set(
        LessonProgress.objects.filter(updated_at__gte=day_cutoff).values_list(
            "user_id", flat=True
        )
    )
    weekly_users = set(
        LessonProgress.objects.filter(updated_at__gte=week_cutoff).values_list(
            "user_id", flat=True
        )
    )
    monthly_users = set(
        LessonProgress.objects.filter(updated_at__gte=month_cutoff).values_list(
            "user_id", flat=True
        )
    )

    # Retention approximation: users active 7/30 days ago that are active today
    seven_days_ago_users = set(
        LessonProgress.objects.filter(
            updated_at__date=(now - timedelta(days=7)).date()
        ).values_list("user_id", flat=True)
    )
    thirty_days_ago_users = set(
        LessonProgress.objects.filter(
            updated_at__date=(now - timedelta(days=30)).date()
        ).values_list("user_id", flat=True)
    )

    retention_7 = (
        len(daily_users & seven_days_ago_users) / len(seven_days_ago_users) * 100
        if seven_days_ago_users
        else 0
    )
    retention_30 = (
        len(daily_users & thirty_days_ago_users) / len(thirty_days_ago_users) * 100
        if thirty_days_ago_users
        else 0
    )

    avg_session_time = (
        LessonProgress.objects.filter(updated_at__gte=month_cutoff)
        .aggregate(avg=Avg("fastest_completion_seconds"))
        .get("avg")
        or 0
    )

    return {
        "dau": len(daily_users),
        "wau": len(weekly_users),
        "mau": len(monthly_users),
        "retention_7": retention_7,
        "retention_30": retention_30,
        "avg_session_time_seconds": avg_session_time,
    }
