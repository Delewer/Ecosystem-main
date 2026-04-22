from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import (
    Classroom,
    ClassroomMembership,
    Lesson,
    LessonProgress,
    Subject,
    Test,
    TestAttempt,
)
from .services.risk_scoring import STREAK_SAFE_DAYS
from .services.teacher_early_warning import (
    RISK_BAND_HIGH,
    build_teacher_early_warning_report,
    send_teacher_early_warning_notification,
)

USER_PASSWORD = "pass1234"
LESSON_CONTENT = "content"
HIGH_SCORE = 90
LOW_SCORE = 20


class TeacherEarlyWarningTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username="teacher", password=USER_PASSWORD
        )
        self.classroom = Classroom.objects.create(
            name="Warning Class", owner=self.teacher
        )
        self.subject = Subject.objects.create(name="Warning Subject")
        self.lesson = Lesson.objects.create(
            subject=self.subject,
            title="Warning Lesson",
            content=LESSON_CONTENT,
            date=timezone.localdate(),
        )
        self.test = Test.objects.create(
            lesson=self.lesson,
            question="What is alert?",
            correct_answer="A",
            wrong_answers=["B", "C"],
        )

        self.high_risk_student = User.objects.create_user(
            username="high_risk", password=USER_PASSWORD
        )
        ClassroomMembership.objects.create(
            classroom=self.classroom,
            user=self.high_risk_student,
            role=ClassroomMembership.ROLE_STUDENT,
            approved=True,
        )
        TestAttempt.objects.create(
            test=self.test,
            user=self.high_risk_student,
            selected_answer="B",
            is_correct=False,
            awarded_points=LOW_SCORE,
        )

        self.low_risk_student = User.objects.create_user(
            username="low_risk", password=USER_PASSWORD
        )
        ClassroomMembership.objects.create(
            classroom=self.classroom,
            user=self.low_risk_student,
            role=ClassroomMembership.ROLE_STUDENT,
            approved=True,
        )
        self.low_risk_student.userprofile.streak = STREAK_SAFE_DAYS
        self.low_risk_student.userprofile.save(update_fields=["streak"])
        LessonProgress.objects.create(
            user=self.low_risk_student, lesson=self.lesson, completed=True
        )
        TestAttempt.objects.create(
            test=self.test,
            user=self.low_risk_student,
            selected_answer="A",
            is_correct=True,
            awarded_points=HIGH_SCORE,
        )

    def test_build_teacher_early_warning_report_flags_high_risk(self):
        result = build_teacher_early_warning_report(self.classroom)

        self.assertTrue(result.success)
        self.assertEqual(result.data["summary"]["flagged_count"], 1)
        alert = result.data["alerts"][0]
        self.assertEqual(alert.student_id, self.high_risk_student.id)
        self.assertEqual(alert.risk_band, RISK_BAND_HIGH)

    def test_send_teacher_early_warning_notification(self):
        result = send_teacher_early_warning_notification(self.classroom)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.data["notification"])
