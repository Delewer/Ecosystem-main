from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils import timezone

from .models import EventLog, Lesson, SeasonalEvent, Subject, UserSeasonalProgress
from .services.gamification import record_lesson_completion
from .services.seasonal_events import (
    DEFAULT_POINTS_PER_LESSON,
    ERROR_INACTIVE_EVENT,
    WARNING_NO_ACTIVE_EVENT,
    enroll_user_in_active_event,
    record_seasonal_progress,
)

USER_PASSWORD = "pass1234"

POINTS_GOAL = 10
REWARD_XP = 25

POINTS_FIRST = 4
POINTS_SECOND = 6

LESSON_POINTS = 7

EXPECTED_ZERO = 0
EXPECTED_ONE = 1
EXPECTED_TWO = 2


class SeasonalEventsTests(TestCase):
    def _create_user(self, username: str) -> User:
        return User.objects.create_user(username=username, password=USER_PASSWORD)

    def _create_event(self, *, start_offset: int, end_offset: int, active: bool):
        today = timezone.localdate()
        return SeasonalEvent.objects.create(
            slug=f"season-{start_offset}-{end_offset}",
            title="Seasonal Sprint",
            description="Seasonal challenge",
            start_date=today + timedelta(days=start_offset),
            end_date=today + timedelta(days=end_offset),
            points_goal=POINTS_GOAL,
            reward_xp=REWARD_XP,
            is_active=active,
        )

    def test_record_progress_without_active_event_warns(self):
        user = self._create_user("seasonal-none")

        result = record_seasonal_progress(
            user=user, points=POINTS_FIRST, source="manual"
        )

        self.assertTrue(result.success)
        self.assertIn(WARNING_NO_ACTIVE_EVENT, result.warnings)
        self.assertEqual(UserSeasonalProgress.objects.count(), EXPECTED_ZERO)

    def test_record_progress_inactive_event_fails(self):
        user = self._create_user("seasonal-inactive")
        event = self._create_event(start_offset=-10, end_offset=-5, active=True)

        result = record_seasonal_progress(
            user=user, points=POINTS_FIRST, source="manual", event=event
        )

        self.assertFalse(result.success)
        self.assertEqual(result.error, ERROR_INACTIVE_EVENT)
        self.assertEqual(UserSeasonalProgress.objects.count(), EXPECTED_ZERO)

    def test_record_progress_completes_and_awards_xp(self):
        user = self._create_user("seasonal-progress")
        self._create_event(start_offset=-1, end_offset=1, active=True)

        first = record_seasonal_progress(
            user=user, points=POINTS_FIRST, source="manual"
        )
        second = record_seasonal_progress(
            user=user, points=POINTS_SECOND, source="manual"
        )

        self.assertTrue(first.success)
        self.assertTrue(second.success)
        progress = UserSeasonalProgress.objects.get(user=user)
        self.assertEqual(progress.points, POINTS_GOAL)
        self.assertIsNotNone(progress.completed_at)
        user.refresh_from_db()
        self.assertEqual(user.userprofile.xp, REWARD_XP)
        self.assertEqual(
            EventLog.objects.filter(
                event_type=EventLog.EVENT_SEASONAL_PROGRESS
            ).count(),
            EXPECTED_TWO,
        )
        self.assertEqual(
            EventLog.objects.filter(
                event_type=EventLog.EVENT_SEASONAL_COMPLETED
            ).count(),
            EXPECTED_ONE,
        )

    def test_enroll_user_in_active_event(self):
        user = self._create_user("seasonal-enroll")
        self._create_event(start_offset=-1, end_offset=1, active=True)

        result = enroll_user_in_active_event(user=user)

        self.assertTrue(result.success)
        progress = result.data["progress"]
        self.assertIsNotNone(progress)
        self.assertEqual(UserSeasonalProgress.objects.count(), EXPECTED_ONE)

    @override_settings(ESTUDY_SEASONAL_POINTS_PER_LESSON=LESSON_POINTS)
    def test_lesson_completion_awards_seasonal_points(self):
        user = self._create_user("seasonal-lesson")
        subject = Subject.objects.create(name="Science")
        lesson = Lesson.objects.create(
            subject=subject,
            title="Experiment",
            content="Content",
            date=timezone.localdate(),
        )
        self._create_event(start_offset=-1, end_offset=1, active=True)

        record_lesson_completion(user=user, lesson=lesson)

        progress = UserSeasonalProgress.objects.get(user=user)
        self.assertEqual(progress.points, LESSON_POINTS)


class SeasonalEventDefaultsTests(TestCase):
    def test_default_points_per_lesson_constant(self):
        self.assertGreater(DEFAULT_POINTS_PER_LESSON, 0)
