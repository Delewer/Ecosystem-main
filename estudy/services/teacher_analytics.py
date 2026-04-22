"""
Продвинутая аналитика для учителей и администраторов
"""
from __future__ import annotations

from datetime import timedelta
from typing import Dict, List

from django.db.models import Avg, Max, Min
from django.utils import timezone

from ..models import (
    AssignmentSubmission,
    ClassAssignment,
    Classroom,
    ClassroomMembership,
    Lesson,
    LessonProgress,
    TestAttempt,
    User,
)
from .difficulty_mismatch import build_lesson_difficulty_analysis


class TeacherAnalytics:
    """Аналитика для учителей"""

    @staticmethod
    def get_classroom_overview(classroom: Classroom) -> Dict:
        """Общий обзор класса"""
        members = classroom.memberships.all()
        total_students = members.filter(role=ClassroomMembership.ROLE_STUDENT).count()

        # Активность за последнюю неделю
        week_ago = timezone.now() - timedelta(days=7)
        active_students = members.filter(last_activity_at__gte=week_ago).count()

        # Средняя успеваемость класса
        student_ids = members.values_list("user_id", flat=True)
        total_attempts = TestAttempt.objects.filter(user_id__in=student_ids).count()
        correct_attempts = TestAttempt.objects.filter(
            user_id__in=student_ids, is_correct=True
        ).count()

        avg_success_rate = (
            (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
        )

        # Статистика по заданиям
        assignments = classroom.assignments.all()
        total_assignments = assignments.count()

        # Средний процент сдачи
        submission_rates = []
        for assignment in assignments:
            submissions = assignment.submissions.count()
            rate = (submissions / total_students * 100) if total_students > 0 else 0
            submission_rates.append(rate)

        avg_submission_rate = (
            sum(submission_rates) / len(submission_rates) if submission_rates else 0
        )

        return {
            "total_students": total_students,
            "active_students": active_students,
            "activity_rate": (active_students / total_students * 100)
            if total_students > 0
            else 0,
            "avg_success_rate": round(avg_success_rate, 1),
            "total_assignments": total_assignments,
            "avg_submission_rate": round(avg_submission_rate, 1),
            "total_tests_taken": total_attempts,
        }

    @staticmethod
    def get_student_detailed_report(student: User, classroom: Classroom = None) -> Dict:
        """Детальный отчет по студенту"""
        # Прогресс по урокам
        completed_lessons = LessonProgress.objects.filter(
            user=student, completed=True
        ).count()

        total_lessons = Lesson.objects.count()
        progress_percent = (
            (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
        )

        # Тесты
        attempts = TestAttempt.objects.filter(user=student)
        total_attempts = attempts.count()
        correct = attempts.filter(is_correct=True).count()
        success_rate = (correct / total_attempts * 100) if total_attempts > 0 else 0

        # Средняя скорость ответа
        avg_time = attempts.aggregate(Avg("time_taken_ms"))["time_taken_ms__avg"] or 0

        # Задания (если класс указан)
        assignments_data = None
        if classroom:
            assignments = ClassAssignment.objects.filter(classroom=classroom)
            submitted = AssignmentSubmission.objects.filter(
                student=student, assignment__classroom=classroom
            ).count()

            assignments_data = {
                "total": assignments.count(),
                "submitted": submitted,
                "pending": assignments.count() - submitted,
                "avg_score": AssignmentSubmission.objects.filter(
                    student=student,
                    assignment__classroom=classroom,
                    score__isnull=False,
                ).aggregate(Avg("score"))["score__avg"]
                or 0,
            }

        # Активность
        profile = student.userprofile
        last_activity = profile.last_activity_at
        days_since_active = None
        if last_activity:
            days_since_active = (timezone.now() - last_activity).days

        return {
            "student": {
                "username": student.username,
                "display_name": profile.display_or_username(),
                "level": profile.level,
                "xp": profile.xp,
                "streak": profile.streak,
            },
            "progress": {
                "completed_lessons": completed_lessons,
                "total_lessons": total_lessons,
                "percent": round(progress_percent, 1),
            },
            "tests": {
                "total_attempts": total_attempts,
                "success_rate": round(success_rate, 1),
                "avg_time_seconds": round(avg_time / 1000, 1) if avg_time else 0,
            },
            "assignments": assignments_data,
            "activity": {
                "last_activity": last_activity,
                "days_since_active": days_since_active,
                "streak": profile.streak,
            },
        }

    @staticmethod
    def get_assignment_analytics(assignment: ClassAssignment) -> Dict:
        """Аналитика по заданию"""
        submissions = assignment.submissions.all()
        total_students = assignment.classroom.memberships.filter(
            role=ClassroomMembership.ROLE_STUDENT
        ).count()

        submitted_count = submissions.count()
        submission_rate = (
            (submitted_count / total_students * 100) if total_students > 0 else 0
        )

        # Оценки
        graded = submissions.filter(score__isnull=False)
        avg_score = graded.aggregate(Avg("score"))["score__avg"] or 0
        max_score = graded.aggregate(Max("score"))["score__max"] or 0
        min_score = graded.aggregate(Min("score"))["score__min"] or 0

        # Распределение оценок
        score_distribution = {
            "excellent": graded.filter(score__gte=90).count(),
            "good": graded.filter(score__gte=70, score__lt=90).count(),
            "satisfactory": graded.filter(score__gte=50, score__lt=70).count(),
            "poor": graded.filter(score__lt=50).count(),
        }

        # Статусы
        status_breakdown = {}
        for status, label in AssignmentSubmission.STATUS_CHOICES:
            count = submissions.filter(status=status).count()
            status_breakdown[status] = {"count": count, "label": label}

        # Не сдавшие
        submitted_user_ids = submissions.values_list("student_id", flat=True)
        not_submitted = (
            assignment.classroom.memberships.filter(
                role=ClassroomMembership.ROLE_STUDENT
            )
            .exclude(user_id__in=submitted_user_ids)
            .values_list("user__username", flat=True)
        )

        return {
            "assignment": {
                "title": assignment.title,
                "due_date": assignment.due_date,
                "points": assignment.points,
            },
            "submission_stats": {
                "total_students": total_students,
                "submitted": submitted_count,
                "submission_rate": round(submission_rate, 1),
                "not_submitted_list": list(not_submitted),
            },
            "score_stats": {
                "avg": round(avg_score, 1),
                "max": max_score,
                "min": min_score,
                "distribution": score_distribution,
            },
            "status_breakdown": status_breakdown,
        }

    @staticmethod
    def identify_struggling_students(
        classroom: Classroom, threshold: float = 50.0
    ) -> List[Dict]:
        """Выявить студентов с трудностями"""
        members = classroom.memberships.filter(role=ClassroomMembership.ROLE_STUDENT)

        struggling = []

        for member in members:
            user = member.user

            # Успеваемость по тестам
            attempts = TestAttempt.objects.filter(user=user)
            total = attempts.count()

            if total < 5:  # Недостаточно данных
                continue

            correct = attempts.filter(is_correct=True).count()
            success_rate = (correct / total * 100) if total > 0 else 0

            # Прогресс по урокам
            completed = LessonProgress.objects.filter(user=user, completed=True).count()

            # Активность
            last_activity = user.userprofile.last_activity_at
            days_inactive = None
            if last_activity:
                days_inactive = (timezone.now() - last_activity).days

            # Критерии для "struggling"
            is_struggling = (
                success_rate < threshold
                or (days_inactive and days_inactive > 7)
                or completed < 3
            )

            if is_struggling:
                struggling.append(
                    {
                        "student": user,
                        "username": user.username,
                        "success_rate": round(success_rate, 1),
                        "completed_lessons": completed,
                        "days_inactive": days_inactive,
                        "total_attempts": total,
                        "concerns": _identify_concerns(
                            success_rate, days_inactive, completed
                        ),
                    }
                )

        # Сортируем по серьезности проблем
        struggling.sort(key=lambda x: x["success_rate"])

        return struggling

    @staticmethod
    def get_lesson_difficulty_analysis(lesson: Lesson) -> Dict:
        """Ранализ сложности урока на основе данных."""
        result = build_lesson_difficulty_analysis(lesson)
        if not result.success:
            return {
                "lesson": lesson.title,
                "insufficient_data": True,
                "error": result.error,
            }
        return result.data.get("analysis", {})


def _identify_concerns(
    success_rate: float, days_inactive: int, completed: int
) -> List[str]:
    """Определить конкретные проблемы студента"""
    concerns = []

    if success_rate < 30:
        concerns.append("Очень низкая успеваемость")
    elif success_rate < 50:
        concerns.append("Низкая успеваемость")

    if days_inactive and days_inactive > 14:
        concerns.append("Долго не заходил")
    elif days_inactive and days_inactive > 7:
        concerns.append("Неактивен больше недели")

    if completed < 3:
        concerns.append("Мало завершенных уроков")

    return concerns


class AdminAnalytics:
    """Аналитика для администраторов"""

    @staticmethod
    def get_platform_statistics() -> Dict:
        """Общая статистика платформы"""
        total_users = User.objects.count()
        total_lessons = Lesson.objects.count()
        total_tests = TestAttempt.objects.count()

        # Активные пользователи (за последние 7 дней)
        week_ago = timezone.now() - timedelta(days=7)
        active_users = User.objects.filter(
            userprofile__last_activity_at__gte=week_ago
        ).count()

        # Средняя успеваемость
        total_attempts = TestAttempt.objects.count()
        correct_attempts = TestAttempt.objects.filter(is_correct=True).count()
        platform_success_rate = (
            (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
        )

        # Завершенные уроки
        total_completions = LessonProgress.objects.filter(completed=True).count()

        return {
            "users": {
                "total": total_users,
                "active_week": active_users,
                "activity_rate": round((active_users / total_users * 100), 1)
                if total_users > 0
                else 0,
            },
            "content": {
                "total_lessons": total_lessons,
                "total_completions": total_completions,
                "avg_completions_per_lesson": round(
                    total_completions / total_lessons, 1
                )
                if total_lessons > 0
                else 0,
            },
            "performance": {
                "total_test_attempts": total_tests,
                "platform_success_rate": round(platform_success_rate, 1),
            },
        }

    @staticmethod
    def get_growth_metrics(days: int = 30) -> Dict:
        """Метрики роста платформы"""
        cutoff = timezone.now() - timedelta(days=days)

        # Новые пользователи
        new_users = User.objects.filter(date_joined__gte=cutoff).count()

        # Новые завершения
        new_completions = LessonProgress.objects.filter(
            completed=True, completed_at__gte=cutoff
        ).count()

        # Рост по дням
        daily_growth = []
        for i in range(days):
            day = timezone.now() - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)

            completions = LessonProgress.objects.filter(
                completed=True, completed_at__gte=day_start, completed_at__lt=day_end
            ).count()

            daily_growth.append({"date": day_start.date(), "completions": completions})

        return {
            "period_days": days,
            "new_users": new_users,
            "new_completions": new_completions,
            "daily_growth": list(reversed(daily_growth)),  # От старых к новым
        }
