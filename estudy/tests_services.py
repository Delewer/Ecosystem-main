from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from .api_exceptions import custom_exception_handler
from .models import EventLog, Lesson, LessonProgress, Subject
from .services.audit_logger import log_event


class ExceptionHandlerTests(TestCase):
    def test_custom_exception_handler_envelope(self):
        exc = NotFound("Missing")
        request = APIRequestFactory().get("/")
        response = custom_exception_handler(exc, {"request": Request(request)})
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"]["status"], 404)


class AuditLoggerTests(TestCase):
    def test_log_event_creates_record(self):
        user = get_user_model().objects.create_user(
            username="tester", password="pass1234"
        )
        log_event(EventLog.EVENT_LOGIN, user=user, metadata={"ip": "127.0.0.1"})
        self.assertEqual(EventLog.objects.count(), 1)
        record = EventLog.objects.first()
        self.assertEqual(record.event_type, EventLog.EVENT_LOGIN)
        self.assertEqual(record.metadata.get("ip"), "127.0.0.1")


class LessonXPIntegrationTests(TestCase):
    def test_lesson_completion_awards_xp(self):
        user = get_user_model().objects.create_user(
            username="learner", password="pass1234"
        )
        subject = Subject.objects.create(name="Math", description="Test")
        lesson = Lesson.objects.create(
            subject=subject,
            title="Integration Lesson",
            slug="integration-lesson",
            content="content",
            date=timezone.now().date(),
            duration_minutes=10,
            xp_reward=75,
        )

        progress = LessonProgress.objects.create(user=user, lesson=lesson)
        progress.mark_completed(award_xp=True)
        user.refresh_from_db()
        self.assertEqual(user.userprofile.xp, lesson.xp_reward)
