"""
Background tasks (Celery-friendly) for notifications, analytics, and achievements.
"""
from __future__ import annotations

try:  # pragma: no cover - Celery may be optional in some deployments
    from celery import shared_task  # type: ignore
except ImportError:  # fallback decorator to avoid crashes if Celery is absent

    def shared_task(*dargs, **dkwargs):
        def decorator(func):
            return func

        return decorator


from django.contrib.auth import get_user_model

from .models import Lesson, NotificationPreference
from .services.achievements import AchievementEngine
from .services.analytics import LessonAnalyticsService
from .services.notifications_enhanced import (
    NotificationTemplate,
    build_weekly_digest,
    delete_old_notifications,
    get_notification_digest,
)
from .services.xp_decay import run_xp_decay

User = get_user_model()


@shared_task
def send_daily_digests():
    """Create daily digest notifications for all users with in-app enabled."""
    users = NotificationPreference.objects.filter(in_app_enabled=True).values_list(
        "user_id", flat=True
    )
    for user_id in users:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            continue
        digest = get_notification_digest(user, period="daily")
        if digest["total"] == 0:
            continue
        NotificationTemplate.create(
            "daily_reminder",
            recipient=user,
            incomplete=digest["total"],
            link_url="/estudy/dashboard/",
        )


@shared_task
def send_weekly_digests():
    """Create weekly digest notifications."""
    users = NotificationPreference.objects.filter(in_app_enabled=True).values_list(
        "user_id", flat=True
    )
    for user_id in users:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            continue
        build_weekly_digest(user)


@shared_task
def recalc_lesson_analytics():
    """Recalculate analytics for all lessons (lightweight loop)."""
    for lesson in Lesson.objects.all().iterator():
        LessonAnalyticsService.update_lesson_analytics(lesson)


@shared_task
def check_achievements():
    """Run achievement engine for all users."""
    for user in User.objects.all().iterator():
        AchievementEngine.check_and_award(user)


@shared_task
def cleanup_notifications(days: int = 30):
    """Delete old read notifications (default 30 days)."""
    return delete_old_notifications(days=days)


@shared_task
def apply_xp_decay():
    """Apply XP decay to inactive profiles."""
    return run_xp_decay()
