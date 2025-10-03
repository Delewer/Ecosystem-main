from __future__ import annotations

from typing import Iterable, Optional

from django.contrib.auth.models import User

from ..models import Notification, NotificationPreference


def _should_send(recipient: User) -> bool:
    prefs, _ = NotificationPreference.objects.get_or_create(user=recipient)
    return prefs.in_app_enabled


def send_notification(
    *,
    recipient: User,
    title: str,
    message: str,
    category: str = Notification.CATEGORY_SYSTEM,
    link_url: str = "",
) -> Notification:
    if not _should_send(recipient):
        return Notification(recipient=recipient, title=title, message=message, category=category, link_url=link_url)
    return Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        category=category,
        link_url=link_url,
    )


def notify_new_lesson(users: Iterable[User], lesson_title: str, link_url: str) -> None:
    for user in users:
        send_notification(
            recipient=user,
            title="Lectie noua te asteapta!",
            message=f"A fost publicata o lectie: {lesson_title}",
            category=Notification.CATEGORY_SYSTEM,
            link_url=link_url,
        )


def notify_feedback(user: User, feedback: str, *, link_url: str = "") -> Notification:
    return send_notification(
        recipient=user,
        title="Ai feedback nou",
        message=feedback,
        category=Notification.CATEGORY_FEEDBACK,
        link_url=link_url,
    )
