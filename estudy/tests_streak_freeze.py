from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import EventLog, StreakFreezeBalance
from .services.streak_freeze import (
    ACTION_STREAK_FREEZE_USED,
    ACTION_STREAK_INCREMENT,
    ACTION_STREAK_RESET,
    MILESTONE_WEEK,
    REWARD_WEEK,
    STREAK_START_VALUE,
    grant_streak_freeze_tokens,
    update_streak_on_activity,
)

USER_PASSWORD = "pass1234"

BASE_STREAK = 3
ONE_DAY = 1

MISSED_DAYS = 1
MISSED_OFFSET_DAYS = MISSED_DAYS + ONE_DAY

RESET_MISSED_DAYS = 2
RESET_OFFSET_DAYS = RESET_MISSED_DAYS + ONE_DAY
RESET_AVAILABLE_TOKENS = 1

TOKENS_TO_GRANT = 2


class StreakFreezeTests(TestCase):
    def _create_user(self, username: str) -> User:
        return User.objects.create_user(username=username, password=USER_PASSWORD)

    def test_increment_streak_on_consecutive_day(self):
        now = timezone.now()
        user = self._create_user("streak-inc")
        profile = user.userprofile
        profile.streak = BASE_STREAK
        profile.last_activity_at = now - timedelta(days=ONE_DAY)
        profile.save(update_fields=["streak", "last_activity_at"])

        result = update_streak_on_activity(user=user, now=now)

        self.assertTrue(result.success)
        snapshot = result.data["snapshot"]
        self.assertEqual(snapshot.action, ACTION_STREAK_INCREMENT)
        profile.refresh_from_db()
        self.assertEqual(profile.streak, BASE_STREAK + 1)

    def test_freeze_token_used_on_gap(self):
        now = timezone.now()
        user = self._create_user("streak-freeze")
        profile = user.userprofile
        profile.streak = BASE_STREAK
        profile.last_activity_at = now - timedelta(days=MISSED_OFFSET_DAYS)
        profile.save(update_fields=["streak", "last_activity_at"])
        StreakFreezeBalance.objects.create(
            user=user,
            available_tokens=MISSED_DAYS,
            used_tokens=0,
            last_awarded_streak=0,
        )

        result = update_streak_on_activity(user=user, now=now)

        self.assertTrue(result.success)
        snapshot = result.data["snapshot"]
        self.assertEqual(snapshot.action, ACTION_STREAK_FREEZE_USED)
        profile.refresh_from_db()
        balance = StreakFreezeBalance.objects.get(user=user)
        self.assertEqual(profile.streak, BASE_STREAK + 1)
        self.assertEqual(balance.available_tokens, 0)
        self.assertEqual(balance.used_tokens, MISSED_DAYS)
        self.assertEqual(
            EventLog.objects.filter(
                event_type=EventLog.EVENT_STREAK_FREEZE_USE
            ).count(),
            1,
        )

    def test_reset_streak_when_tokens_insufficient(self):
        now = timezone.now()
        user = self._create_user("streak-reset")
        profile = user.userprofile
        profile.streak = BASE_STREAK
        profile.last_activity_at = now - timedelta(days=RESET_OFFSET_DAYS)
        profile.save(update_fields=["streak", "last_activity_at"])
        StreakFreezeBalance.objects.create(
            user=user,
            available_tokens=RESET_AVAILABLE_TOKENS,
            used_tokens=0,
            last_awarded_streak=0,
        )

        result = update_streak_on_activity(user=user, now=now)

        self.assertTrue(result.success)
        snapshot = result.data["snapshot"]
        self.assertEqual(snapshot.action, ACTION_STREAK_RESET)
        profile.refresh_from_db()
        balance = StreakFreezeBalance.objects.get(user=user)
        self.assertEqual(profile.streak, STREAK_START_VALUE)
        self.assertEqual(balance.available_tokens, RESET_AVAILABLE_TOKENS)
        self.assertEqual(
            EventLog.objects.filter(
                event_type=EventLog.EVENT_STREAK_FREEZE_USE
            ).count(),
            0,
        )

    def test_grant_streak_freeze_tokens_logs_event(self):
        user = self._create_user("streak-grant")

        result = grant_streak_freeze_tokens(
            user=user, amount=TOKENS_TO_GRANT, reason="admin_grant"
        )

        self.assertTrue(result.success)
        balance = StreakFreezeBalance.objects.get(user=user)
        self.assertEqual(balance.available_tokens, TOKENS_TO_GRANT)
        self.assertEqual(
            EventLog.objects.filter(
                event_type=EventLog.EVENT_STREAK_FREEZE_GRANT
            ).count(),
            1,
        )

    def test_milestone_awards_tokens(self):
        now = timezone.now()
        user = self._create_user("streak-milestone")
        profile = user.userprofile
        profile.streak = MILESTONE_WEEK - ONE_DAY
        profile.last_activity_at = now - timedelta(days=ONE_DAY)
        profile.save(update_fields=["streak", "last_activity_at"])

        result = update_streak_on_activity(user=user, now=now)

        self.assertTrue(result.success)
        snapshot = result.data["snapshot"]
        self.assertEqual(snapshot.action, ACTION_STREAK_INCREMENT)
        balance = StreakFreezeBalance.objects.get(user=user)
        self.assertEqual(balance.available_tokens, REWARD_WEEK)
        self.assertEqual(
            EventLog.objects.filter(
                event_type=EventLog.EVENT_STREAK_FREEZE_GRANT
            ).count(),
            1,
        )
