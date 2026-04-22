from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import Lesson, LessonProgress, Subject, Test, TestAttempt
from .services.risk_scoring import (
    PERCENT_MAX,
    PERCENT_MIN,
    RISK_BAND_HIGH,
    RISK_BAND_LOW,
    SCORE_DECIMALS,
    STREAK_SAFE_DAYS,
    WEIGHT_COMPLETION,
    WEIGHT_SCORE,
    WEIGHT_STREAK,
    WEIGHT_SUM,
    build_student_risk_score,
)

USER_PASSWORD = "pass1234"
LESSON_CONTENT = "content"

HIGH_SCORE = 90
LOW_SCORE = 20

EXPECTED_COMPLETED_LESSONS = 2
EXPECTED_TOTAL_LESSONS = 2


class StudentRiskScoringTests(TestCase):
    def setUp(self):
        self.subject = Subject.objects.create(name="Risk Subject")
        self.lesson_one = Lesson.objects.create(
            subject=self.subject,
            title="Risk Lesson 1",
            content=LESSON_CONTENT,
            date=timezone.localdate(),
        )
        self.lesson_two = Lesson.objects.create(
            subject=self.subject,
            title="Risk Lesson 2",
            content=LESSON_CONTENT,
            date=timezone.localdate(),
        )

    def _create_test_with_attempt(self, user, score: int):
        test = Test.objects.create(
            lesson=self.lesson_one,
            question="What is risk?",
            correct_answer="A",
            wrong_answers=["B", "C"],
        )
        return TestAttempt.objects.create(
            test=test,
            user=user,
            selected_answer="A",
            is_correct=True,
            awarded_points=score,
        )

    def test_low_risk_band(self):
        user = User.objects.create_user(username="low", password=USER_PASSWORD)
        LessonProgress.objects.create(user=user, lesson=self.lesson_one, completed=True)
        LessonProgress.objects.create(user=user, lesson=self.lesson_two, completed=True)
        self._create_test_with_attempt(user, HIGH_SCORE)
        user.userprofile.streak = STREAK_SAFE_DAYS
        user.userprofile.save(update_fields=["streak"])

        result = build_student_risk_score(user)
        snapshot = result.data["snapshot"]

        expected_completion_rate = (
            EXPECTED_COMPLETED_LESSONS / EXPECTED_TOTAL_LESSONS
        ) * PERCENT_MAX
        expected_completion_risk = PERCENT_MAX - expected_completion_rate
        expected_score_risk = PERCENT_MAX - HIGH_SCORE
        expected_streak_risk = PERCENT_MIN
        expected_risk_score = (
            expected_completion_risk * WEIGHT_COMPLETION
            + expected_score_risk * WEIGHT_SCORE
            + expected_streak_risk * WEIGHT_STREAK
        )
        expected_risk_score = round(expected_risk_score / WEIGHT_SUM, SCORE_DECIMALS)

        self.assertTrue(result.success)
        self.assertEqual(snapshot.risk_band, RISK_BAND_LOW)
        self.assertEqual(snapshot.risk_score, expected_risk_score)
        self.assertEqual(result.warnings, ())

    def test_high_risk_band(self):
        user = User.objects.create_user(username="high", password=USER_PASSWORD)
        self._create_test_with_attempt(user, LOW_SCORE)
        user.userprofile.streak = 0
        user.userprofile.save(update_fields=["streak"])

        result = build_student_risk_score(user)
        snapshot = result.data["snapshot"]

        expected_completion_rate = PERCENT_MIN
        expected_completion_risk = PERCENT_MAX - expected_completion_rate
        expected_score_risk = PERCENT_MAX - LOW_SCORE
        expected_streak_risk = PERCENT_MAX
        expected_risk_score = (
            expected_completion_risk * WEIGHT_COMPLETION
            + expected_score_risk * WEIGHT_SCORE
            + expected_streak_risk * WEIGHT_STREAK
        )
        expected_risk_score = round(expected_risk_score / WEIGHT_SUM, SCORE_DECIMALS)

        self.assertTrue(result.success)
        self.assertEqual(snapshot.risk_band, RISK_BAND_HIGH)
        self.assertEqual(snapshot.risk_score, expected_risk_score)
