from __future__ import annotations

from typing import Dict, List, Tuple

from django.db.models import Count
from django.utils import timezone

from ..models import (
    Badge,
    Lesson,
    LessonProgress,
    Mission,
    UserBadge,
    UserMission,
    check_and_award_rewards,
)

DEFAULT_MISSIONS: Tuple[dict, ...] = (
    {
        "code": "daily-complete-lesson",
        "title": "Complete o lectie",
        "description": "Finalizeaza cel putin o lectie astazi",
        "frequency": Mission.FREQ_DAILY,
        "target_value": 1,
        "reward_points": 40,
        "icon": "fa-check-double",
        "color": "#22c55e",
    },
    {
        "code": "weekly-quiz-master",
        "title": "Campion la quiz-uri",
        "description": "Raspunde corect la trei quiz-uri in aceasta saptamana",
        "frequency": Mission.FREQ_WEEKLY,
        "target_value": 3,
        "reward_points": 80,
        "icon": "fa-trophy",
        "color": "#f59e0b",
    },
    {
        "code": "project-progress",
        "title": "Pas spre proiect",
        "description": "Incarca un proiect sau un mini-proiect",
        "frequency": Mission.FREQ_ONCE,
        "target_value": 1,
        "reward_points": 120,
        "icon": "fa-rocket",
        "color": "#6366f1",
    },
)


def ensure_default_missions() -> None:
    for payload in DEFAULT_MISSIONS:
        Mission.objects.get_or_create(code=payload["code"], defaults=payload)


def ensure_user_missions(user) -> List[UserMission]:
    ensure_default_missions()
    missions = Mission.objects.filter(is_active=True)
    user_missions = []
    for mission in missions:
        user_mission, _ = UserMission.objects.get_or_create(user=user, mission=mission)
        user_missions.append(user_mission)
    return user_missions


def record_lesson_completion(user, lesson: Lesson, seconds_spent: int | None = None) -> Dict:
    progress, _ = LessonProgress.objects.get_or_create(user=user, lesson=lesson)
    progress.mark_completed(seconds_spent=seconds_spent)
    check_and_award_rewards(user)

    missions = ensure_user_missions(user)
    for mission in missions:
        if mission.mission.code == "daily-complete-lesson":
            mission.register_progress()

    return build_overall_progress(user)


def build_overall_progress(user) -> Dict[str, float | int]:
    total_lessons = Lesson.objects.count()
    completed = LessonProgress.objects.filter(user=user, completed=True).count()
    percent = round((completed / total_lessons) * 100, 2) if total_lessons else 0
    return {
        "total": total_lessons,
        "completed": completed,
        "percent": percent,
    }


def get_badge_summary(user) -> Dict[str, List[UserBadge]]:
    badges = UserBadge.objects.filter(user=user).select_related("badge").order_by("-awarded_at")
    highlighted = badges[:3]
    return {
        "all": list(badges),
        "highlighted": list(highlighted),
        "count": badges.count(),
    }


def get_mission_context(user) -> Dict[str, List[UserMission]]:
    missions = ensure_user_missions(user)
    daily = [m for m in missions if m.mission.frequency == Mission.FREQ_DAILY]
    weekly = [m for m in missions if m.mission.frequency == Mission.FREQ_WEEKLY]
    once = [m for m in missions if m.mission.frequency == Mission.FREQ_ONCE]
    return {
        "daily": daily,
        "weekly": weekly,
        "special": once,
    }


def get_leaderboard_snapshot(limit: int = 10) -> List[dict]:
    leaders = (
        LessonProgress.objects.filter(completed=True)
        .values("user__username")
        .annotate(total=Count("id"))
        .order_by("-total")[:limit]
    )
    return [
        {
            "position": index + 1,
            "username": item["user__username"],
            "score": item["total"],
        }
        for index, item in enumerate(leaders)
    ]
