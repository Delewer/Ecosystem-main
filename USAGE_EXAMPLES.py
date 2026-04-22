"""
Примеры использования новых модулей аналитики и геймификации
"""

# ============================================
# 1. РАСШИРЕННАЯ АНАЛИТИКА СТУДЕНТОВ
# ============================================

from estudy.services.assessment_enhanced import (
    generate_personalized_practice_plan,
    get_adaptive_difficulty_recommendation,
    get_learning_velocity,
    get_student_performance_analytics,
)


# Получить полную аналитику студента
def example_student_analytics(user):
    analytics = get_student_performance_analytics(user)

    print(f"Успеваемость: {analytics['success_rate']}%")
    print(f"Всего попыток: {analytics['total_attempts']}")
    print(f"Среднее время: {analytics['average_time_seconds']} сек")

    # Слабые темы
    if analytics["weak_topics"]:
        print("\nСлабые темы:")
        for topic in analytics["weak_topics"]:
            print(f"- {topic['lesson'].title}: {topic['success_rate']}%")

    # Прогресс за неделю
    print(f"\nПрогресс за неделю: {analytics['weekly_progress']}%")

    return analytics


# Адаптивная сложность
def example_adaptive_difficulty(user, lesson):
    recommended_difficulty = get_adaptive_difficulty_recommendation(user, lesson)

    if recommended_difficulty != lesson.difficulty:
        print(
            f"Рекомендуем изменить сложность с {lesson.difficulty} на {recommended_difficulty}"
        )

    return recommended_difficulty


# Персональный план обучения
def example_study_plan(user):
    plan = generate_personalized_practice_plan(user, days=7)

    print("Ваш план на неделю:")
    for item in plan:
        print(f"День {item['day']}: {item['lesson'].title}")
        print(f"  Причина: {item['reason']}")
        print(f"  Приоритет: {item['priority']}")
        print(f"  Время: {item['estimated_time']} мин\n")

    return plan


# Скорость обучения
def example_learning_velocity(user):
    velocity = get_learning_velocity(user, days=30)

    print(f"За последние 30 дней:")
    print(f"- Завершено уроков: {velocity['lessons_completed']}")
    print(f"- Уроков в неделю: {velocity['lessons_per_week']}")
    print(f"- Тренд: {velocity['trend']}")

    return velocity


# ============================================
# 2. УМНЫЕ УВЕДОМЛЕНИЯ
# ============================================

from estudy.models import Notification, User
from estudy.services.notifications_enhanced import (
    NotificationTemplate,
    get_notification_digest,
    send_bulk_notification,
    send_streak_reminder,
)


# Создать уведомление по шаблону
def example_template_notification(user):
    # Уведомление о новом уровне
    NotificationTemplate.create("level_up", recipient=user, level=5)

    # Уведомление о значке
    NotificationTemplate.create(
        "badge_earned",
        recipient=user,
        badge="Мастер Python",
        description="Завершил 10 уроков по Python",
    )

    # Уведомление учителя
    NotificationTemplate.create(
        "teacher_feedback",
        recipient=user,
        teacher="Иван Иванов",
        assignment="Домашнее задание #5",
        link_url="/estudy/classroom/assignments/5/",
    )


# Массовая рассылка
def example_bulk_notification(classroom):
    students = User.objects.filter(
        classroom_memberships__classroom=classroom,
        classroom_memberships__role="student",
    )

    count = send_bulk_notification(
        users=students,
        title="Новое задание!",
        message="Вам назначено новое задание по Python. Срок сдачи: 15 ноября.",
        category=Notification.CATEGORY_SYSTEM,
    )

    print(f"Отправлено {count} уведомлений")
    return count


# Дайджест уведомлений
def example_notification_digest(user):
    # Дневной дайджест
    daily_digest = get_notification_digest(user, period="daily")
    print(f"За сегодня: {daily_digest['total']} уведомлений")
    print(f"Непрочитанных: {daily_digest['unread']}")

    # Недельный дайджест
    weekly_digest = get_notification_digest(user, period="weekly")
    print(f"\nЗа неделю: {weekly_digest['total']} уведомлений")

    for category, data in weekly_digest["by_category"].items():
        print(f"{data['label']}: {data['count']}")

    return daily_digest, weekly_digest


# Напоминание о серии
def example_streak_reminder_check():
    from datetime import timedelta

    from django.utils import timezone

    # Проверяем всех пользователей
    users = User.objects.filter(userprofile__streak__gt=0)

    for user in users:
        notification = send_streak_reminder(user)
        if notification:
            print(f"Напоминание отправлено: {user.username}")


# ============================================
# 3. СИСТЕМА ДОСТИЖЕНИЙ
# ============================================

from estudy.services.achievements import (
    AchievementEngine,
    ChallengeManager,
    LeaderboardManager,
    generate_competitive_missions,
)


# Проверка и выдача достижений
def example_check_achievements(user):
    awarded = AchievementEngine.check_and_award(user)

    if awarded:
        print(f"Получено новых достижений: {len(awarded)}")
        for badge in awarded:
            print(f"- {badge.badge.name}: {badge.badge.description}")
    else:
        print("Новых достижений нет")

    return awarded


# Работа с челленджами
def example_challenges(user):
    # Получить активные челленджи
    active = ChallengeManager.get_active_challenges()

    for challenge in active:
        # Прогресс пользователя
        progress = ChallengeManager.get_user_challenge_progress(user, challenge)

        print(f"\n{challenge.title}")
        print(f"Прогресс: {progress['completed']}/{progress['target']}")
        print(f"Завершено: {progress['progress_percent']}%")
        print(f"Дней осталось: {progress['days_left']}")

        # Проверка выполнения
        if ChallengeManager.check_challenge_completion(user, challenge):
            print("✓ Челлендж выполнен!")
            awarded = ChallengeManager.award_challenge(user, challenge)
            if awarded:
                print(f"Награда выдана: {challenge.points} XP")


# Недельный челлендж
def example_create_weekly_challenge():
    import datetime

    current_week = datetime.date.today().isocalendar()[1]
    current_year = datetime.date.today().year

    challenge = ChallengeManager.create_weekly_challenge(current_week, current_year)
    print(f"Создан челлендж: {challenge.title}")
    print(f"Период: {challenge.start_date} - {challenge.end_date}")

    return challenge


# Рейтинги
def example_leaderboards(user, classroom=None):
    # Глобальный рейтинг
    global_leaders = LeaderboardManager.get_global_leaderboard(period="week", limit=10)

    print("Топ-10 недели:")
    for leader in global_leaders:
        print(f"{leader['rank']}. {leader['username']}: {leader['total_xp']} XP")

    # Рейтинг класса
    if classroom:
        class_leaders = LeaderboardManager.get_classroom_leaderboard(
            classroom, period="week"
        )

        print(f"\nРейтинг класса {classroom.name}:")
        for leader in class_leaders:
            print(
                f"{leader['rank']}. {leader['username']}: {leader['lessons_completed']} уроков"
            )

    # Ранг пользователя
    rank = LeaderboardManager.get_user_rank(user, scope="global")
    print(f"\nВаш глобальный ранг: #{rank}")

    return global_leaders, rank


# Создание соревновательных миссий
def example_competitive_missions():
    missions = generate_competitive_missions()

    print("Созданы миссии:")
    for mission in missions:
        print(f"- {mission.title}: {mission.description}")

    return missions


# ============================================
# 4. АНАЛИТИКА ДЛЯ УЧИТЕЛЕЙ
# ============================================

from estudy.services.teacher_analytics import AdminAnalytics, TeacherAnalytics


# Обзор класса
def example_classroom_overview(classroom):
    overview = TeacherAnalytics.get_classroom_overview(classroom)

    print(f"Класс: {classroom.name}")
    print(f"Всего студентов: {overview['total_students']}")
    print(
        f"Активных на неделе: {overview['active_students']} ({overview['activity_rate']}%)"
    )
    print(f"Средняя успеваемость: {overview['avg_success_rate']}%")
    print(f"Заданий: {overview['total_assignments']}")
    print(f"Средний % сдачи: {overview['avg_submission_rate']}%")

    return overview


# Детальный отчет по студенту
def example_student_report(student, classroom):
    report = TeacherAnalytics.get_student_detailed_report(student, classroom)

    print(f"\n=== Отчет по студенту {report['student']['username']} ===")
    print(f"Уровень: {report['student']['level']}")
    print(f"XP: {report['student']['xp']}")
    print(f"Серия: {report['student']['streak']} дней")

    print(
        f"\nПрогресс: {report['progress']['completed_lessons']}/{report['progress']['total_lessons']}"
    )
    print(f"Успеваемость: {report['tests']['success_rate']}%")

    if report["assignments"]:
        print(
            f"\nЗадания: {report['assignments']['submitted']}/{report['assignments']['total']}"
        )
        print(f"Средняя оценка: {report['assignments']['avg_score']}")

    if report["activity"]["days_since_active"] is not None:
        print(
            f"\nПоследняя активность: {report['activity']['days_since_active']} дней назад"
        )

    return report


# Аналитика задания
def example_assignment_analytics(assignment):
    analytics = TeacherAnalytics.get_assignment_analytics(assignment)

    print(f"Задание: {analytics['assignment']['title']}")
    print(
        f"Сдали: {analytics['submission_stats']['submitted']}/{analytics['submission_stats']['total_students']}"
    )
    print(f"% сдачи: {analytics['submission_stats']['submission_rate']}%")

    print(f"\nОценки:")
    print(f"Средняя: {analytics['score_stats']['avg']}")
    print(f"Макс: {analytics['score_stats']['max']}")
    print(f"Мин: {analytics['score_stats']['min']}")

    dist = analytics["score_stats"]["distribution"]
    print(f"\nРаспределение:")
    print(f"Отлично (90+): {dist['excellent']}")
    print(f"Хорошо (70-89): {dist['good']}")
    print(f"Удовл (50-69): {dist['satisfactory']}")
    print(f"Плохо (<50): {dist['poor']}")

    if analytics["submission_stats"]["not_submitted_list"]:
        print(
            f"\nНе сдали: {', '.join(analytics['submission_stats']['not_submitted_list'])}"
        )

    return analytics


# Выявление отстающих
def example_struggling_students(classroom):
    struggling = TeacherAnalytics.identify_struggling_students(
        classroom, threshold=60.0
    )

    if struggling:
        print(f"Найдено студентов с трудностями: {len(struggling)}\n")

        for student in struggling:
            print(f"{student['username']}:")
            print(f"  Успеваемость: {student['success_rate']}%")
            print(f"  Завершено уроков: {student['completed_lessons']}")

            if student["days_inactive"]:
                print(f"  Неактивен: {student['days_inactive']} дней")

            print(f"  Проблемы:")
            for concern in student["concerns"]:
                print(f"    - {concern}")
            print()
    else:
        print("Все студенты справляются!")

    return struggling


# Анализ сложности урока
def example_lesson_difficulty_analysis(lesson):
    analysis = TeacherAnalytics.get_lesson_difficulty_analysis(lesson)

    if analysis.get("insufficient_data"):
        print(f"Недостаточно данных для анализа урока '{lesson.title}'")
        return None

    print(f"Урок: {analysis['lesson']}")
    print(f"Заявленная сложность: {analysis['declared_difficulty']}")
    print(f"Реальная сложность: {analysis['real_difficulty']}")
    print(f"Успеваемость: {analysis['success_rate']}%")
    print(f"Среднее время: {analysis['avg_time_seconds']} сек")
    print(f"\nРекомендация: {analysis['recommendation']}")

    return analysis


# Статистика платформы (для админов)
def example_platform_statistics():
    stats = AdminAnalytics.get_platform_statistics()

    print("=== Статистика платформы ===")
    print(f"\nПользователи:")
    print(f"  Всего: {stats['users']['total']}")
    print(f"  Активных за неделю: {stats['users']['active_week']}")
    print(f"  Активность: {stats['users']['activity_rate']}%")

    print(f"\nКонтент:")
    print(f"  Уроков: {stats['content']['total_lessons']}")
    print(f"  Завершений: {stats['content']['total_completions']}")
    print(f"  Среднее на урок: {stats['content']['avg_completions_per_lesson']}")

    print(f"\nУспеваемость:")
    print(f"  Всего попыток тестов: {stats['performance']['total_test_attempts']}")
    print(f"  Успеваемость платформы: {stats['performance']['platform_success_rate']}%")

    return stats


# Метрики роста
def example_growth_metrics():
    growth = AdminAnalytics.get_growth_metrics(days=30)

    print(f"Рост за {growth['period_days']} дней:")
    print(f"Новых пользователей: {growth['new_users']}")
    print(f"Новых завершений: {growth['new_completions']}")

    # Последние 7 дней
    print("\nПоследние 7 дней:")
    for day in growth["daily_growth"][-7:]:
        print(f"{day['date']}: {day['completions']} завершений")

    return growth


# ============================================
# 5. ИНТЕГРАЦИЯ В ПРЕДСТАВЛЕНИЯ
# ============================================

# Пример представления с использованием новых сервисов
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from estudy.services.assessment_enhanced import get_student_performance_analytics
from estudy.services.achievements import AchievementEngine

@login_required
def enhanced_dashboard(request):
    user = request.user
    
    # Проверяем достижения
    new_badges = AchievementEngine.check_and_award(user)
    
    # Получаем аналитику
    analytics = get_student_performance_analytics(user)
    
    # Генерируем план
    study_plan = generate_personalized_practice_plan(user, days=7)
    
    context = {
        'new_badges': new_badges,
        'analytics': analytics,
        'study_plan': study_plan,
    }
    
    return render(request, 'estudy/enhanced_dashboard.html', context)
"""

# ============================================
# 6. CELERY ЗАДАЧИ (опционально)
# ============================================

"""
# estudy/tasks.py
from celery import shared_task
from django.contrib.auth.models import User
from .services.achievements import AchievementEngine
from .services.notifications_enhanced import schedule_assignment_reminders

@shared_task
def check_achievements_daily():
    \"\"\"Ежедневная проверка достижений всех пользователей\"\"\"
    users = User.objects.filter(is_active=True)
    count = 0
    
    for user in users:
        badges = AchievementEngine.check_and_award(user)
        count += len(badges)
    
    return f"Awarded {count} new badges"

@shared_task
def send_assignment_reminders():
    \"\"\"Отправка напоминаний о приближающихся дедлайнах\"\"\"
    count = schedule_assignment_reminders()
    return f"Sent {count} reminders"

# Настройка в celery.py:
app.conf.beat_schedule = {
    'check-achievements-daily': {
        'task': 'estudy.tasks.check_achievements_daily',
        'schedule': crontab(hour=0, minute=0),  # Каждый день в полночь
    },
    'send-assignment-reminders': {
        'task': 'estudy.tasks.send_assignment_reminders',
        'schedule': crontab(hour=9, minute=0),  # Каждый день в 9 утра
    },
}
"""

if __name__ == "__main__":
    print("Примеры использования новых модулей готовы!")
    print("Импортируйте нужные функции и используйте в своем коде.")
