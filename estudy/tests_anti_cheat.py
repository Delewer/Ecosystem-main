from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import Lesson, Subject, Test, TestAttempt
from .services.anti_cheat import (
    CODE_SIGNAL_HIGH_SIMILARITY,
    CODE_SIMILARITY_THRESHOLD,
    TEST_FAST_INCORRECT_MS,
    TEST_REPEAT_INCORRECT_MS,
    TEST_REPEAT_INCORRECT_THRESHOLD,
    TEST_SIGNAL_FAST_INCORRECT,
    TEST_SIGNAL_RAPID_INCORRECTS,
    analyze_code_submission,
    analyze_test_attempt,
)

USER_PASSWORD = "pass1234"
RECENT_OFFSET_MINUTES = 5
TIME_OFFSET_MS = 1
FAST_INCORRECT_TIME_MS = TEST_FAST_INCORRECT_MS - TIME_OFFSET_MS
CORRECT_FAST_TIME_MS = FAST_INCORRECT_TIME_MS
REPEAT_TIME_MS = TEST_REPEAT_INCORRECT_MS - TIME_OFFSET_MS


class AntiCheatTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="anti", password=USER_PASSWORD)
        subject = Subject.objects.create(name="Subject")
        lesson = Lesson.objects.create(
            subject=subject,
            title="Lesson",
            content="Content",
            date=timezone.localdate(),
        )
        self.test = Test.objects.create(
            lesson=lesson,
            question="Q?",
            correct_answer="yes",
            wrong_answers=["no"],
        )

    def test_fast_incorrect_is_flagged(self):
        result = analyze_test_attempt(
            user=self.user,
            test=self.test,
            is_correct=False,
            time_taken_ms=FAST_INCORRECT_TIME_MS,
        )

        self.assertTrue(result.success)
        self.assertTrue(result.data["suspicious"])
        self.assertIn(TEST_SIGNAL_FAST_INCORRECT, result.data["signals"])

    def test_repeat_incorrect_is_flagged(self):
        now = timezone.now()
        for _ in range(TEST_REPEAT_INCORRECT_THRESHOLD):
            attempt = TestAttempt.objects.create(
                user=self.user,
                test=self.test,
                selected_answer="no",
                is_correct=False,
            )
            TestAttempt.objects.filter(pk=attempt.pk).update(
                created_at=now - timedelta(minutes=RECENT_OFFSET_MINUTES)
            )

        recent_attempts = TestAttempt.objects.filter(user=self.user, test=self.test)
        result = analyze_test_attempt(
            user=self.user,
            test=self.test,
            is_correct=False,
            time_taken_ms=REPEAT_TIME_MS,
            recent_attempts=recent_attempts,
        )

        self.assertTrue(result.success)
        self.assertTrue(result.data["suspicious"])
        self.assertIn(TEST_SIGNAL_RAPID_INCORRECTS, result.data["signals"])

    def test_correct_attempt_not_flagged(self):
        result = analyze_test_attempt(
            user=self.user,
            test=self.test,
            is_correct=True,
            time_taken_ms=CORRECT_FAST_TIME_MS,
        )

        self.assertTrue(result.success)
        self.assertFalse(result.data["suspicious"])

    def test_code_similarity_flagged(self):
        code = "print('hi')"
        solution = "print('hi')"
        result = analyze_code_submission(code=code, solution=solution)

        self.assertTrue(result.success)
        self.assertTrue(result.data["suspicious"])
        self.assertIn(CODE_SIGNAL_HIGH_SIMILARITY, result.data["signals"])
        self.assertGreaterEqual(
            result.data["similarity_score"], CODE_SIMILARITY_THRESHOLD
        )

    def test_code_similarity_missing_solution(self):
        result = analyze_code_submission(code="print('hi')", solution="")

        self.assertTrue(result.success)
        self.assertFalse(result.data["suspicious"])
        self.assertIsNone(result.data["similarity_score"])
