from __future__ import annotations

from django.utils import timezone

from ..models import CoopSession, Lesson
from .feature_flags import is_enabled as feature_enabled
from .gamification import record_lesson_completion
from .service_result import BaseServiceResult

FEATURE_KEY = "coop_mode_enabled"


def create_coop_session(host, lesson: Lesson) -> BaseServiceResult:
    """Create a new cooperative session for a lesson.

    Returns session_code on success.
    """
    if not feature_enabled(FEATURE_KEY, user=host):
        return BaseServiceResult.fail("Cooperative mode is not enabled.")

    session = CoopSession.objects.create(host=host, lesson=lesson)
    return BaseServiceResult.ok(
        data={
            "session_code": session.session_code,
            "session_id": session.pk,
            "lesson_title": lesson.title,
            "status": session.status,
        }
    )


def join_coop_session(guest, session_code: str) -> BaseServiceResult:
    """Join an existing coop session by its 6-character code."""
    if not feature_enabled(FEATURE_KEY, user=guest):
        return BaseServiceResult.fail("Cooperative mode is not enabled.")

    code = session_code.strip().upper()
    session = (
        CoopSession.objects.filter(
            session_code=code,
            status=CoopSession.STATUS_WAITING,
        )
        .select_related("host", "lesson")
        .first()
    )

    if session is None:
        return BaseServiceResult.fail("Session not found or no longer available.")

    if session.host == guest:
        return BaseServiceResult.fail("You cannot join your own session.")

    session.guest = guest
    session.status = CoopSession.STATUS_ACTIVE
    session.save(update_fields=["guest", "status"])

    return BaseServiceResult.ok(
        data={
            "session_id": session.pk,
            "session_code": session.session_code,
            "host_username": session.host.username,
            "lesson_title": session.lesson.title,
            "lesson_slug": session.lesson.slug,
            "status": session.status,
        }
    )


def complete_coop_session(session: CoopSession) -> BaseServiceResult:
    """Mark a coop session as completed and award XP to both participants."""
    if session.status == CoopSession.STATUS_COMPLETED:
        return BaseServiceResult.fail("Session is already completed.")

    if not session.guest:
        return BaseServiceResult.fail("Session has no guest yet.")

    session.status = CoopSession.STATUS_COMPLETED
    session.completed_at = timezone.now()
    session.save(update_fields=["status", "completed_at"])

    record_lesson_completion(session.host, session.lesson)
    record_lesson_completion(session.guest, session.lesson)

    return BaseServiceResult.ok(
        data={
            "session_id": session.pk,
            "host_username": session.host.username,
            "guest_username": session.guest.username,
            "lesson_title": session.lesson.title,
        }
    )
