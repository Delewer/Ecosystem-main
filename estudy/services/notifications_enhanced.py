"""
Notification templates and helpers.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Dict, List

from django.utils import timezone

from ..models import Lesson, Notification, NotificationPreference, User


class NotificationTemplate:
    """Templates for platform notifications."""

    TEMPLATES = {
        "streak_milestone": {
            "title": "Serie de {streak} zile!",
            "message": (
                "Excelent! Inveti {streak} zile la rand. Continua in acelasi ritm!"
            ),
            "category": Notification.CATEGORY_PROGRESS,
        },
        "level_up": {
            "title": "Nivel nou {level}!",
            "message": (
                "Felicitari! Acum esti la nivelul {level}. "
                "Te asteapta provocari noi!"
            ),
            "category": Notification.CATEGORY_PROGRESS,
        },
        "assignment_due_soon": {
            "title": "Tema trebuie predata curand",
            "message": 'Tema "{assignment}" trebuie predata peste {days} zile. Nu uita!',
            "category": Notification.CATEGORY_SYSTEM,
        },
        "new_comment": {
            "title": "Comentariu nou",
            "message": '{username} a comentat in discutia ta "{thread}"',
            "category": Notification.CATEGORY_COMMUNITY,
        },
        "project_reviewed": {
            "title": "Proiect verificat",
            "message": 'Proiectul tau "{project}" a fost verificat! Scor: {score}/100',
            "category": Notification.CATEGORY_FEEDBACK,
        },
        "badge_earned": {
            "title": "Insigna noua!",
            "message": 'Ai primit insigna "{badge}"! {description}',
            "category": Notification.CATEGORY_PROGRESS,
        },
        "daily_reminder": {
            "title": "E timpul sa inveti!",
            "message": ("Salut! Ai {incomplete} lectii nefinalizate. Incepem?"),
            "category": Notification.CATEGORY_SYSTEM,
        },
        "weekly_summary": {
            "title": "Rezultatele tale pe saptamana",
            "message": (
                "Saptamana aceasta: {lessons} lectii, {xp} XP, " "{badges} insigne noi!"
            ),
            "category": Notification.CATEGORY_PROGRESS,
        },
        "teacher_feedback": {
            "title": "Feedback nou de la profesor",
            "message": 'Profesorul {teacher} a lasat feedback la "{assignment}"',
            "category": Notification.CATEGORY_FEEDBACK,
        },
        "teacher_early_warning": {
            "title": "Atentie: {count} elevi au nevoie de sprijin",
            "message": (
                "Clasa {classroom} are elevi cu risc: {students}. "
                "Verifica progresul si planifica sprijin."
            ),
            "category": Notification.CATEGORY_FEEDBACK,
        },
        "parent_report": {
            "title": "Raport despre progresul copilului",
            "message": "{child} a finalizat {lessons} lectii. Reusita: {rate}%",
            "category": Notification.CATEGORY_SYSTEM,
        },
    }

    @classmethod
    def create(cls, template_key: str, recipient: User, **kwargs) -> Notification:
        """Create a notification from a template."""
        template = cls.TEMPLATES.get(template_key)
        if not template:
            raise ValueError(f"Template {template_key} not found")

        title = template["title"].format(**kwargs)
        message = template["message"].format(**kwargs)

        return Notification.objects.create(
            recipient=recipient,
            title=title,
            message=message,
            category=template["category"],
            link_url=kwargs.get("link_url", ""),
        )


def send_bulk_notification(
    users: List[User], title: str, message: str, category: str = None
):
    """Send one notification to multiple users."""
    notifications = []
    for user in users:
        pref, _ = NotificationPreference.objects.get_or_create(user=user)
        if pref.in_app_enabled:
            notifications.append(
                Notification(
                    recipient=user,
                    title=title,
                    message=message,
                    category=category or Notification.CATEGORY_SYSTEM,
                )
            )

    Notification.objects.bulk_create(notifications)
    return len(notifications)


def get_notification_digest(user, period: str = "daily") -> Dict:
    """Return a notification digest for the selected period."""
    if period == "daily":
        cutoff = timezone.now() - timedelta(days=1)
    elif period == "weekly":
        cutoff = timezone.now() - timedelta(days=7)
    else:
        cutoff = timezone.now() - timedelta(days=30)

    notifications = Notification.objects.filter(recipient=user, created_at__gte=cutoff)

    digest = {
        "period": period,
        "total": notifications.count(),
        "unread": notifications.filter(read_at__isnull=True).count(),
        "by_category": {},
    }

    for category, label in Notification.CATEGORY_CHOICES:
        count = notifications.filter(category=category).count()
        if count > 0:
            digest["by_category"][category] = {
                "count": count,
                "label": label,
                "recent": list(notifications.filter(category=category)[:3]),
            }

    return digest


def enforce_quiet_hours(user, notification: Notification) -> bool:
    """Return True if notification should be suppressed due to quiet hours."""
    pref, _ = NotificationPreference.objects.get_or_create(user=user)
    quiet_start = getattr(pref, "quiet_hours_start", None)
    quiet_end = getattr(pref, "quiet_hours_end", None)
    if quiet_start is None or quiet_end is None:
        return False
    now = timezone.localtime().time()
    if quiet_start < quiet_end:
        return quiet_start <= now <= quiet_end
    return now >= quiet_start or now <= quiet_end


def send_with_quiet_hours(user: User, title: str, message: str, category: str = None):
    """Send notification respecting quiet hours and preferences."""
    pref, _ = NotificationPreference.objects.get_or_create(user=user)
    if not pref.in_app_enabled:
        return None
    notification = Notification(
        recipient=user,
        title=title,
        message=message,
        category=category or Notification.CATEGORY_SYSTEM,
    )
    if enforce_quiet_hours(user, notification):
        return None
    notification.save()
    return notification


def build_weekly_digest(user: User):
    """Create or return weekly digest notification."""
    digest = get_notification_digest(user, period="weekly")
    if digest["total"] == 0:
        return None
    return NotificationTemplate.create(
        "weekly_summary",
        recipient=user,
        lessons=digest["total"],
        xp=0,
        badges=digest.get("by_category", {})
        .get(Notification.CATEGORY_PROGRESS, {})
        .get("count", 0),
    )


def mark_all_as_read(user, category: str = None):
    """Mark all matching notifications as read."""
    queryset = Notification.objects.filter(recipient=user, read_at__isnull=True)

    if category:
        queryset = queryset.filter(category=category)

    count = queryset.update(read_at=timezone.now())
    return count


def delete_old_notifications(days: int = 30):
    """Delete old read notifications."""
    cutoff = timezone.now() - timedelta(days=days)
    deleted = Notification.objects.filter(
        read_at__isnull=False, read_at__lt=cutoff
    ).delete()
    return deleted[0]


def get_notification_stats(user) -> Dict:
    """Return notification statistics for a user."""
    notifications = Notification.objects.filter(recipient=user)

    total = notifications.count()
    unread = notifications.filter(read_at__isnull=True).count()
    read = total - unread

    read_notifs = notifications.filter(read_at__isnull=False)
    avg_read_time = None
    if read_notifs.exists():
        times = []
        for notif in read_notifs:
            if notif.read_at and notif.created_at:
                delta = (notif.read_at - notif.created_at).total_seconds()
                times.append(delta)
        if times:
            avg_read_time = sum(times) / len(times) / 3600

    return {
        "total": total,
        "unread": unread,
        "read": read,
        "read_rate": (read / total * 100) if total > 0 else 0,
        "avg_read_time_hours": round(avg_read_time, 1) if avg_read_time else None,
    }


def send_streak_reminder(user):
    """Send a reminder before a learning streak expires."""
    profile = user.userprofile
    last_activity = profile.last_activity_at

    if not last_activity:
        return None

    hours_since = (timezone.now() - last_activity).total_seconds() / 3600

    if 20 <= hours_since < 24 and profile.streak > 0:
        incomplete_lessons = Lesson.objects.exclude(
            progress_records__user=user,
            progress_records__completed=True,
        ).count()
        return NotificationTemplate.create(
            "daily_reminder",
            recipient=user,
            incomplete=incomplete_lessons,
            link_url="/estudy/dashboard/",
        )

    return None


def notify_parent_about_child_progress(parent: User, child: User):
    """Send a child progress report to a parent."""
    from ..services.assessment_enhanced import get_student_performance_analytics

    analytics = get_student_performance_analytics(child)

    return NotificationTemplate.create(
        "parent_report",
        recipient=parent,
        child=child.username,
        lessons=analytics["recent_attempts"],
        rate=analytics["success_rate"],
    )


def schedule_assignment_reminders():
    """Schedule reminders for assignments due tomorrow."""
    from ..models import AssignmentSubmission, ClassAssignment

    tomorrow = timezone.now().date() + timedelta(days=1)
    assignments = ClassAssignment.objects.filter(due_date=tomorrow)

    count = 0
    for assignment in assignments:
        classroom_members = assignment.classroom.memberships.all()
        submitted_students = AssignmentSubmission.objects.filter(
            assignment=assignment
        ).values_list("student_id", flat=True)

        for membership in classroom_members:
            if membership.user.id not in submitted_students:
                NotificationTemplate.create(
                    "assignment_due_soon",
                    recipient=membership.user,
                    assignment=assignment.title,
                    days=1,
                    link_url=f"/estudy/classroom/{assignment.classroom.id}/",
                )
                count += 1

    return count
