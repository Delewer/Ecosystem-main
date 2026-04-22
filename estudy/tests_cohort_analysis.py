from datetime import datetime, time, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import Lesson, LessonProgress, Subject
from .services.cohort_analysis import (
    PERCENT_MAX,
    PERIOD_WEEKLY,
    SCORE_DECIMALS,
    build_user_cohort_retention,
)

USER_PASSWORD = "pass1234"
DAYS_PER_WEEK = 7
WEEKS_AGO = 2
WEEK_DAYS = DAYS_PER_WEEK - 1
MID_WEEK_OFFSET = 1
MAX_PERIODS = 1

COHORT_ONE_USERS = 2
COHORT_TWO_USERS = 1
COHORT_ONE_WEEK1_ACTIVE = 2
COHORT_ONE_WEEK2_ACTIVE = 1
COHORT_TWO_WEEK1_ACTIVE = 1
COHORT_TWO_WEEK2_ACTIVE = 0


class CohortAnalysisTests(TestCase):
    def setUp(self):
        today = timezone.localdate()
        start_offset = today.weekday() + (WEEKS_AGO * DAYS_PER_WEEK)
        self.week1_start = today - timedelta(days=start_offset)
        self.week2_start = self.week1_start + timedelta(days=DAYS_PER_WEEK)
        self.week2_end = self.week2_start + timedelta(days=WEEK_DAYS)

        self.subject = Subject.objects.create(name="Cohort Subject")
        self.lesson_one = Lesson.objects.create(
            subject=self.subject,
            title="Cohort Lesson 1",
            content="content",
            date=self.week1_start,
        )
        self.lesson_two = Lesson.objects.create(
            subject=self.subject,
            title="Cohort Lesson 2",
            content="content",
            date=self.week1_start,
        )

    def _as_aware(self, date_value):
        return timezone.make_aware(datetime.combine(date_value, time.min))

    def _create_user(self, username, joined_date):
        user = User.objects.create_user(username=username, password=USER_PASSWORD)
        User.objects.filter(pk=user.pk).update(date_joined=joined_date)
        return user

    def _create_progress(self, user, lesson, updated_date):
        if isinstance(updated_date, datetime):
            updated_at = updated_date
        else:
            updated_at = self._as_aware(updated_date)
        progress = LessonProgress.objects.create(
            user=user, lesson=lesson, completed=True
        )
        LessonProgress.objects.filter(pk=progress.pk).update(updated_at=updated_at)
        return progress

    def test_weekly_cohort_retention(self):
        user_one = self._create_user("u1", self._as_aware(self.week1_start))
        user_two = self._create_user(
            "u2", self._as_aware(self.week1_start + timedelta(days=MID_WEEK_OFFSET))
        )
        user_three = self._create_user(
            "u3", self._as_aware(self.week2_start + timedelta(days=MID_WEEK_OFFSET))
        )

        week1_mid = self.week1_start + timedelta(days=MID_WEEK_OFFSET)
        week2_mid = self.week2_start + timedelta(days=MID_WEEK_OFFSET)

        self._create_progress(user_one, self.lesson_one, week1_mid)
        self._create_progress(user_one, self.lesson_two, week2_mid)
        self._create_progress(user_two, self.lesson_one, week1_mid)
        self._create_progress(user_three, self.lesson_one, week2_mid)

        result = build_user_cohort_retention(
            start=self.week1_start,
            end=self.week2_end,
            period=PERIOD_WEEKLY,
            max_periods=MAX_PERIODS,
        )

        self.assertTrue(result.success)
        cohorts = result.data["cohorts"]
        self.assertEqual(len(cohorts), 2)

        cohort_one = cohorts[0]
        cohort_two = cohorts[1]

        self.assertEqual(cohort_one.cohort_size, COHORT_ONE_USERS)
        self.assertEqual(cohort_two.cohort_size, COHORT_TWO_USERS)

        self.assertEqual(cohort_one.periods[0].active_users, COHORT_ONE_WEEK1_ACTIVE)
        self.assertEqual(cohort_one.periods[1].active_users, COHORT_ONE_WEEK2_ACTIVE)
        self.assertEqual(cohort_two.periods[0].active_users, COHORT_TWO_WEEK1_ACTIVE)
        self.assertEqual(cohort_two.periods[1].active_users, COHORT_TWO_WEEK2_ACTIVE)

        expected_week1 = round(
            (COHORT_ONE_WEEK1_ACTIVE / COHORT_ONE_USERS) * PERCENT_MAX, SCORE_DECIMALS
        )
        expected_week2 = round(
            (COHORT_ONE_WEEK2_ACTIVE / COHORT_ONE_USERS) * PERCENT_MAX, SCORE_DECIMALS
        )
        self.assertEqual(cohort_one.periods[0].retention_rate, expected_week1)
        self.assertEqual(cohort_one.periods[1].retention_rate, expected_week2)

    def test_empty_users_returns_warning(self):
        result = build_user_cohort_retention(
            start=self.week1_start,
            end=self.week2_end,
            period=PERIOD_WEEKLY,
            max_periods=MAX_PERIODS,
        )

        self.assertTrue(result.success)
        self.assertEqual(result.data["cohorts"], [])
        self.assertIn("no_users", result.warnings)
