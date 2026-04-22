"""
Расширенная система достижений, челленджей и соревнований
"""
from __future__ import annotations

from datetime import timedelta
from typing import Dict, List, Optional

from django.db.models import Count, Q, Sum
from django.utils import timezone

from ..models import (
    Badge,
    ChallengeAttempt,
    DailyChallenge,
    LessonProgress,
    Mission,
    TestAttempt,
    UserBadge,
    UserProfile,
)


class AchievementEngine:
    """Движок для проверки и выдачи достижений"""

    ACHIEVEMENT_RULES = {
        # Достижения за скорость
        "speed_demon": {
            "name": "Демон скорости",
            "description": "Ответь на 10 тестов с бонусом за скорость",
            "icon": "fa-bolt",
            "color": "#f59e0b",
            "check": lambda user: TestAttempt.objects.filter(
                user=user, earned_bonus=True
            ).count()
            >= 10,
        },
        # Достижения за серии
        "week_warrior": {
            "name": "Недельный воин",
            "description": "Учись 7 дней подряд",
            "icon": "fa-fire",
            "color": "#ef4444",
            "check": lambda user: user.userprofile.streak >= 7,
        },
        "month_master": {
            "name": "Мастер месяца",
            "description": "Учись 30 дней подряд",
            "icon": "fa-crown",
            "color": "#fbbf24",
            "check": lambda user: user.userprofile.streak >= 30,
        },
        # Достижения за количество
        "century_club": {
            "name": "Клуб сотни",
            "description": "Набери 100 уроков",
            "icon": "fa-hundred-points",
            "color": "#8b5cf6",
            "check": lambda user: LessonProgress.objects.filter(
                user=user, completed=True
            ).count()
            >= 100,
        },
        # Достижения за разнообразие
        "subject_explorer": {
            "name": "Исследователь предметов",
            "description": "Пройди уроки по 5 разным предметам",
            "icon": "fa-compass",
            "color": "#06b6d4",
            "check": lambda user: LessonProgress.objects.filter(
                user=user, completed=True
            )
            .values("lesson__subject")
            .distinct()
            .count()
            >= 5,
        },
        # Достижения за помощь сообществу
        "helpful_hero": {
            "name": "Герой помощи",
            "description": "Оставь 50 полезных комментариев",
            "icon": "fa-hands-helping",
            "color": "#10b981",
            "check": lambda user: user.replies.count() >= 50,
        },
        # Достижения за совершенство
        "perfectionist": {
            "name": "Перфекционист",
            "description": "Ответь правильно на 20 тестов подряд",
            "icon": "fa-star",
            "color": "#eab308",
            "check": lambda user: _check_test_streak(user, 20),
        },
        # Достижения за время суток
        "night_owl": {
            "name": "Ночная сова",
            "description": "Заверши 10 уроков после 22:00",
            "icon": "fa-moon",
            "color": "#6366f1",
            "check": lambda user: _check_night_lessons(user, 10),
        },
        "early_bird": {
            "name": "Ранняя птичка",
            "description": "Заверши 10 уроков до 8:00",
            "icon": "fa-sun",
            "color": "#f97316",
            "check": lambda user: _check_morning_lessons(user, 10),
        },
    }

    @classmethod
    def check_and_award(cls, user) -> List[UserBadge]:
        """Проверить все достижения и выдать новые"""
        awarded = []

        for slug, rule in cls.ACHIEVEMENT_RULES.items():
            # Проверяем, есть ли уже этот значок
            if UserBadge.objects.filter(user=user, badge__slug=slug).exists():
                continue

            # Проверяем условие
            if rule["check"](user):
                # Создаем или получаем значок
                badge, _ = Badge.objects.get_or_create(
                    slug=slug,
                    defaults={
                        "name": rule["name"],
                        "description": rule["description"],
                        "icon": rule["icon"],
                        "color": rule["color"],
                        "xp_reward": 100,
                    },
                )

                # Выдаем пользователю
                user_badge = UserBadge.objects.create(
                    user=user, badge=badge, reason=rule["description"]
                )

                # Добавляем XP
                user.userprofile.add_xp(
                    badge.xp_reward, reason=f"Achievement: {badge.name}"
                )

                awarded.append(user_badge)

        return awarded


def _check_test_streak(user, required: int) -> bool:
    """Проверка серии правильных ответов"""
    recent_attempts = TestAttempt.objects.filter(user=user).order_by("-created_at")[
        :required
    ]

    if recent_attempts.count() < required:
        return False

    return all(attempt.is_correct for attempt in recent_attempts)


def _check_night_lessons(user, required: int) -> bool:
    """Проверка ночных уроков"""
    night_completions = LessonProgress.objects.filter(
        user=user, completed=True, completed_at__hour__gte=22
    ).count()
    return night_completions >= required


def _check_morning_lessons(user, required: int) -> bool:
    """Проверка утренних уроков"""
    morning_completions = LessonProgress.objects.filter(
        user=user, completed=True, completed_at__hour__lt=8
    ).count()
    return morning_completions >= required


class ChallengeManager:
    """Управление ежедневными и недельными челленджами"""

    @staticmethod
    def create_weekly_challenge(week_number: int, year: int) -> DailyChallenge:
        """Создать недельный челлендж"""
        # Вычисляем даты
        import datetime

        jan_4 = datetime.date(year, 1, 4)
        week_start = jan_4 + timedelta(weeks=week_number - 1)
        week_start = week_start - timedelta(days=week_start.weekday())
        week_end = week_start + timedelta(days=6)

        challenge = DailyChallenge.objects.create(
            code=f"weekly-{year}-{week_number}",
            title=f"Недельный челлендж {week_number}",
            description="Заверши 5 уроков за неделю и получи бонус!",
            points=200,
            start_date=week_start,
            end_date=week_end,
        )
        return challenge

    @staticmethod
    def check_challenge_completion(user, challenge: DailyChallenge) -> bool:
        """Проверить выполнение челленджа"""
        # Пример: для недельного челленджа проверяем 5 уроков
        completed = LessonProgress.objects.filter(
            user=user,
            completed=True,
            completed_at__gte=challenge.start_date,
            completed_at__lte=challenge.end_date,
        ).count()

        return completed >= 5

    @staticmethod
    def award_challenge(user, challenge: DailyChallenge):
        """Выдать награду за челлендж"""
        attempt, created = ChallengeAttempt.objects.get_or_create(
            user=user, challenge=challenge, defaults={"is_successful": True}
        )

        if created:
            # Выдаем очки
            user.userprofile.add_xp(
                challenge.points, reason=f"Challenge: {challenge.title}"
            )
            return True
        return False

    @staticmethod
    def get_active_challenges() -> List[DailyChallenge]:
        """Получить активные челленджи"""
        today = timezone.now().date()
        return DailyChallenge.objects.filter(start_date__lte=today, end_date__gte=today)

    @staticmethod
    def get_user_challenge_progress(user, challenge: DailyChallenge) -> Dict:
        """Прогресс пользователя в челлендже"""
        completed_lessons = LessonProgress.objects.filter(
            user=user,
            completed=True,
            completed_at__gte=challenge.start_date,
            completed_at__lte=challenge.end_date,
        ).count()

        target = 5  # Можно сделать динамическим
        progress_percent = min(100, (completed_lessons / target) * 100)

        return {
            "challenge": challenge,
            "completed": completed_lessons,
            "target": target,
            "progress_percent": round(progress_percent, 1),
            "is_completed": completed_lessons >= target,
            "days_left": (challenge.end_date - timezone.now().date()).days,
        }


class LeaderboardManager:
    """Управление рейтингами"""

    @staticmethod
    def get_global_leaderboard(
        period: str = "all_time", limit: int = 100
    ) -> List[Dict]:
        """Глобальный рейтинг"""
        if period == "week":
            week_ago = timezone.now() - timedelta(days=7)
            queryset = LessonProgress.objects.filter(
                completed=True, completed_at__gte=week_ago
            )
        elif period == "month":
            month_ago = timezone.now() - timedelta(days=30)
            queryset = LessonProgress.objects.filter(
                completed=True, completed_at__gte=month_ago
            )
        else:  # all_time
            queryset = LessonProgress.objects.filter(completed=True)

        leaders = (
            queryset.values("user__username")
            .annotate(total=Count("id"), total_xp=Sum("points_earned"))
            .order_by("-total_xp", "-total")[:limit]
        )

        return [
            {
                "rank": idx + 1,
                "username": item["user__username"],
                "lessons_completed": item["total"],
                "total_xp": item["total_xp"] or 0,
            }
            for idx, item in enumerate(leaders)
        ]

    @staticmethod
    def get_classroom_leaderboard(classroom, period: str = "all_time") -> List[Dict]:
        """Рейтинг класса"""
        members = classroom.memberships.values_list("user", flat=True)

        if period == "week":
            week_ago = timezone.now() - timedelta(days=7)
            date_filter = Q(completed_at__gte=week_ago)
        elif period == "month":
            month_ago = timezone.now() - timedelta(days=30)
            date_filter = Q(completed_at__gte=month_ago)
        else:
            date_filter = Q()

        leaders = (
            LessonProgress.objects.filter(user__in=members, completed=True)
            .filter(date_filter)
            .values("user__username")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        return [
            {
                "rank": idx + 1,
                "username": item["user__username"],
                "lessons_completed": item["total"],
            }
            for idx, item in enumerate(leaders)
        ]

    @staticmethod
    def get_user_rank(user, scope: str = "global") -> Optional[int]:
        """Получить ранг пользователя"""
        if scope == "global":
            # Считаем всех, кто впереди
            user_xp = user.userprofile.xp
            ahead = UserProfile.objects.filter(xp__gt=user_xp).count()
            return ahead + 1

        return None


def generate_competitive_missions() -> List[Mission]:
    """Создать соревновательные миссии"""
    missions_data = [
        {
            "code": "top-10-leaderboard",
            "title": "Попади в топ-10",
            "description": "Займи место в топ-10 глобального рейтинга",
            "frequency": Mission.FREQ_ONCE,
            "target_value": 1,
            "reward_points": 500,
            "icon": "fa-trophy",
            "color": "#fbbf24",
        },
        {
            "code": "beat-the-class",
            "title": "Первый в классе",
            "description": "Стань лучшим в своем классе за неделю",
            "frequency": Mission.FREQ_WEEKLY,
            "target_value": 1,
            "reward_points": 300,
            "icon": "fa-medal",
            "color": "#f97316",
        },
        {
            "code": "speed-champion",
            "title": "Чемпион скорости",
            "description": "Получи 5 бонусов за скорость за один день",
            "frequency": Mission.FREQ_DAILY,
            "target_value": 5,
            "reward_points": 150,
            "icon": "fa-stopwatch",
            "color": "#06b6d4",
        },
    ]

    created = []
    for data in missions_data:
        mission, _ = Mission.objects.get_or_create(code=data["code"], defaults=data)
        created.append(mission)

    return created
