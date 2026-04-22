"""
Расширенная система оценивания с аналитикой и адаптивным обучением
"""
from __future__ import annotations

import random
from datetime import timedelta
from typing import Dict, List

from django.db.models import Avg, Count
from django.utils import timezone

from ..models import Lesson, LessonProgress, Test, TestAttempt


def get_student_performance_analytics(user) -> Dict:
    """
    Детальная аналитика успеваемости студента
    """
    attempts = TestAttempt.objects.filter(user=user)

    total_attempts = attempts.count()
    correct_attempts = attempts.filter(is_correct=True).count()
    success_rate = (
        (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
    )

    # Средняя скорость ответа
    avg_time = (
        attempts.filter(time_taken_ms__gt=0).aggregate(avg=Avg("time_taken_ms"))["avg"]
        or 0
    )

    # Анализ по сложности
    difficulty_stats = {}
    for difficulty in ["beginner", "intermediate", "advanced"]:
        diff_attempts = attempts.filter(test__difficulty=difficulty)
        diff_correct = diff_attempts.filter(is_correct=True).count()
        diff_total = diff_attempts.count()
        difficulty_stats[difficulty] = {
            "total": diff_total,
            "correct": diff_correct,
            "rate": (diff_correct / diff_total * 100) if diff_total > 0 else 0,
        }

    # Слабые темы (уроки с низкой успеваемостью)
    weak_lessons = []
    for lesson in Lesson.objects.all():
        lesson_attempts = attempts.filter(test__lesson=lesson)
        lesson_total = lesson_attempts.count()
        if lesson_total >= 3:  # Минимум 3 попытки для статистики
            lesson_correct = lesson_attempts.filter(is_correct=True).count()
            success = (lesson_correct / lesson_total * 100) if lesson_total > 0 else 0
            if success < 60:  # Порог слабой темы
                weak_lessons.append(
                    {
                        "lesson": lesson,
                        "success_rate": success,
                        "attempts": lesson_total,
                    }
                )

    weak_lessons.sort(key=lambda x: x["success_rate"])

    # Прогресс за последнюю неделю
    week_ago = timezone.now() - timedelta(days=7)
    recent_attempts = attempts.filter(created_at__gte=week_ago)
    recent_correct = recent_attempts.filter(is_correct=True).count()
    recent_total = recent_attempts.count()
    weekly_progress = (recent_correct / recent_total * 100) if recent_total > 0 else 0

    return {
        "total_attempts": total_attempts,
        "success_rate": round(success_rate, 1),
        "average_time_seconds": round(avg_time / 1000, 1) if avg_time else 0,
        "difficulty_breakdown": difficulty_stats,
        "weak_topics": weak_lessons[:5],  # Топ-5 слабых тем
        "weekly_progress": round(weekly_progress, 1),
        "recent_attempts": recent_total,
        "bonus_earned_count": attempts.filter(earned_bonus=True).count(),
    }


def get_adaptive_difficulty_recommendation(user, lesson: Lesson) -> str:
    """
    Рекомендация уровня сложности на основе истории пользователя
    """
    # Получаем историю попыток по этому уроку
    attempts = TestAttempt.objects.filter(user=user, test__lesson=lesson)

    if not attempts.exists():
        return lesson.difficulty  # Используем стандартную сложность

    # Вычисляем успешность
    total = attempts.count()
    correct = attempts.filter(is_correct=True).count()
    success_rate = (correct / total * 100) if total > 0 else 0

    # Логика адаптации
    if success_rate >= 90:
        # Отлично справляется - можно повысить сложность
        difficulty_order = ["beginner", "intermediate", "advanced"]
        current_index = difficulty_order.index(lesson.difficulty)
        if current_index < len(difficulty_order) - 1:
            return difficulty_order[current_index + 1]
    elif success_rate < 50:
        # Сложно - понизить сложность
        difficulty_order = ["beginner", "intermediate", "advanced"]
        current_index = difficulty_order.index(lesson.difficulty)
        if current_index > 0:
            return difficulty_order[current_index - 1]

    return lesson.difficulty


def get_test_insights(test: Test) -> Dict:
    """
    Статистика по конкретному тесту (для учителей)
    """
    attempts = TestAttempt.objects.filter(test=test)
    total_attempts = attempts.count()

    if total_attempts == 0:
        return {
            "total_attempts": 0,
            "success_rate": 0,
            "average_time": 0,
            "common_mistakes": [],
            "difficulty_rating": "unknown",
        }

    correct_count = attempts.filter(is_correct=True).count()
    success_rate = correct_count / total_attempts * 100

    # Средняя скорость
    avg_time = (
        attempts.filter(time_taken_ms__gt=0).aggregate(avg=Avg("time_taken_ms"))["avg"]
        or 0
    )

    # Частые ошибки
    wrong_attempts = attempts.filter(is_correct=False)
    common_mistakes = (
        wrong_attempts.values("selected_answer")
        .annotate(count=Count("id"))
        .order_by("-count")[:3]
    )

    # Оценка сложности
    if success_rate >= 80:
        difficulty_rating = "easy"
    elif success_rate >= 50:
        difficulty_rating = "medium"
    else:
        difficulty_rating = "hard"

    return {
        "total_attempts": total_attempts,
        "success_rate": round(success_rate, 1),
        "average_time_seconds": round(avg_time / 1000, 1),
        "common_mistakes": list(common_mistakes),
        "difficulty_rating": difficulty_rating,
        "bonus_achievers": attempts.filter(earned_bonus=True).count(),
    }


def generate_personalized_practice_plan(user, days: int = 7) -> List[Dict]:
    """
    Генерация персонализированного плана обучения на N дней
    """
    analytics = get_student_performance_analytics(user)
    weak_topics = analytics["weak_topics"]

    # Получаем некомплетные уроки
    completed_ids = LessonProgress.objects.filter(
        user=user, completed=True
    ).values_list("lesson_id", flat=True)

    incomplete_lessons = Lesson.objects.exclude(id__in=completed_ids).order_by(
        "difficulty", "date"
    )

    plan = []

    # Распределяем по дням
    # Приоритет - слабые темы
    for item in weak_topics[:days]:
        plan.append(
            {
                "day": len(plan) + 1,
                "lesson": item["lesson"],
                "reason": f'Слабая тема (успешность {item["success_rate"]:.0f}%)',
                "priority": "high",
                "estimated_time": item["lesson"].duration_minutes,
            }
        )

    # Добавляем новые уроки
    for lesson in incomplete_lessons[: days - len(plan)]:
        plan.append(
            {
                "day": len(plan) + 1,
                "lesson": lesson,
                "reason": "Новый материал",
                "priority": "medium",
                "estimated_time": lesson.duration_minutes,
            }
        )

    return plan


def compare_students(user1, user2) -> Dict:
    """
    Сравнение двух студентов (для родителей/учителей)
    """
    analytics1 = get_student_performance_analytics(user1)
    analytics2 = get_student_performance_analytics(user2)

    return {
        "user1": {"username": user1.username, "stats": analytics1},
        "user2": {"username": user2.username, "stats": analytics2},
        "comparison": {
            "success_rate_diff": analytics1["success_rate"]
            - analytics2["success_rate"],
            "speed_diff": analytics1["average_time_seconds"]
            - analytics2["average_time_seconds"],
            "attempts_diff": analytics1["total_attempts"]
            - analytics2["total_attempts"],
        },
    }


def get_learning_velocity(user, days: int = 30) -> Dict:
    """
    Скорость обучения - сколько уроков завершается за период
    """
    cutoff = timezone.now() - timedelta(days=days)

    completed = LessonProgress.objects.filter(
        user=user, completed=True, completed_at__gte=cutoff
    ).count()

    lessons_per_week = (completed / days) * 7 if days > 0 else 0

    # Тренд - сравниваем с предыдущим периодом
    prev_cutoff = timezone.now() - timedelta(days=days * 2)
    prev_completed = LessonProgress.objects.filter(
        user=user,
        completed=True,
        completed_at__gte=prev_cutoff,
        completed_at__lt=cutoff,
    ).count()

    trend = (
        "increasing"
        if completed > prev_completed
        else "decreasing"
        if completed < prev_completed
        else "stable"
    )

    return {
        "lessons_completed": completed,
        "lessons_per_week": round(lessons_per_week, 1),
        "period_days": days,
        "trend": trend,
        "previous_period": prev_completed,
    }


def get_question_bank(difficulty: str | None = None, limit: int = 10) -> List[Test]:
    """
    Return a randomized question bank filtered by difficulty when provided.
    """
    queryset = Test.objects.all()
    if difficulty:
        queryset = queryset.filter(difficulty=difficulty)
    ids = list(queryset.values_list("id", flat=True))
    random.shuffle(ids)
    selected = ids[:limit]
    return list(Test.objects.filter(id__in=selected))


def sample_questions_for_lesson(lesson: Lesson, limit: int = 5) -> List[Test]:
    """
    Grab a small randomized subset of questions for a lesson.
    """
    qs = Test.objects.filter(lesson=lesson).order_by("?")[:limit]
    return list(qs)
