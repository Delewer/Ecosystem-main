from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import Lesson, LessonProgress, Subject, Test, TestAttempt
from .services.assessment import process_test_attempt


class AssessmentServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="assessor", password="pw")
        self.subject = Subject.objects.create(name="Comp", description="Comp")
        today = timezone.localdate()
        self.lesson = Lesson.objects.create(
            subject=self.subject, title="T", content="c", date=today
        )
        self.test = Test.objects.create(
            lesson=self.lesson,
            question="Q?",
            correct_answer="yes",
            wrong_answers=["no"],
            points=30,
            bonus_time_threshold=10,
        )

    def test_correct_answer_records_attempt_and_completes_lesson(self):
        resp = process_test_attempt(self.user, self.test, "yes", time_taken_ms=5000)
        self.assertTrue(resp["is_correct"])
        self.assertIn("lesson_completed", resp)
        self.assertTrue(resp["lesson_completed"])
        ta = TestAttempt.objects.get(user=self.user, test=self.test)
        self.assertEqual(ta.awarded_points, 30)
        lp = LessonProgress.objects.get(user=self.user, lesson=self.lesson)
        self.assertTrue(lp.completed)

    def test_incorrect_answer_records_attempt_no_completion(self):
        resp = process_test_attempt(self.user, self.test, "no", time_taken_ms=15000)
        self.assertFalse(resp["is_correct"])
        self.assertFalse(resp["lesson_completed"])
        ta = TestAttempt.objects.get(user=self.user, test=self.test)
        self.assertEqual(ta.awarded_points, 0)
