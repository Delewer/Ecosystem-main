from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import Lesson, LessonFeedback, LessonHealthScore, LessonProgress, Subject
from .services.lesson_health import (
    PERCENT_MAX,
    QUALITY_MAX_SCORE,
    SCORE_DECIMALS,
    WEIGHT_COMPLETION,
    WEIGHT_QUALITY,
    WEIGHT_RATING,
    WEIGHT_SUM,
    refresh_all_lesson_health_scores,
    update_lesson_health_score,
)

RATING_VALUE = 4
COMPLETED_COUNT = 1
TOTAL_COUNT = 2
EXPECTED_COMPLETION_RATE = (COMPLETED_COUNT / TOTAL_COUNT) * PERCENT_MAX
USER_PASSWORD = "pass1234"


class LessonHealthScoreTests(TestCase):
    def setUp(self):
        self.subject = Subject.objects.create(name="Health Subject")
        self.lesson = Lesson.objects.create(
            subject=self.subject,
            title="Health Lesson",
            content="content",
            date=timezone.localdate(),
        )
        self.user_one = User.objects.create_user(username="u1", password=USER_PASSWORD)
        self.user_two = User.objects.create_user(username="u2", password=USER_PASSWORD)
        LessonProgress.objects.create(
            user=self.user_one, lesson=self.lesson, completed=True
        )
        LessonProgress.objects.create(
            user=self.user_two, lesson=self.lesson, completed=False
        )
        LessonFeedback.objects.create(
            lesson=self.lesson,
            user=self.user_one,
            content_quality=RATING_VALUE,
            difficulty_appropriate=RATING_VALUE,
            examples_helpful=RATING_VALUE,
            overall_rating=RATING_VALUE,
            would_recommend=True,
        )

    def test_health_score_created(self):
        result = update_lesson_health_score(self.lesson)
        health = result.data["health"]

        self.assertTrue(result.success)
        self.assertEqual(LessonHealthScore.objects.count(), 1)
        self.assertEqual(health.completion_rate, EXPECTED_COMPLETION_RATE)
        self.assertEqual(health.avg_rating, RATING_VALUE)

        expected_quality_percent = (RATING_VALUE / QUALITY_MAX_SCORE) * PERCENT_MAX
        expected_rating_percent = expected_quality_percent
        expected_score = (
            expected_quality_percent * WEIGHT_QUALITY
            + EXPECTED_COMPLETION_RATE * WEIGHT_COMPLETION
            + expected_rating_percent * WEIGHT_RATING
        )
        expected_score = round(expected_score / WEIGHT_SUM, SCORE_DECIMALS)
        self.assertEqual(health.score, expected_score)

    def test_refresh_all_health_scores(self):
        result = refresh_all_lesson_health_scores()

        self.assertTrue(result.success)
        self.assertEqual(result.data["updated"], 1)
