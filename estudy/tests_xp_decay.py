from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils import timezone

from .models import EventLog, UserProfile
from .services.xp_decay import (
    DEFAULT_DECAY_START_DAYS,
    DEFAULT_MIN_LEVEL,
    DEFAULT_MIN_XP,
    LEVEL_BASE_XP,
    LEVEL_GROWTH_FACTOR,
    WARNING_DECAY_DISABLED,
    WARNING_NO_DECAY,
    apply_xp_decay,
    run_xp_decay,
)

USER_PASSWORD = "pass1234"

DISABLED_EXTRA_DAYS = 2
DISABLED_INACTIVE_DAYS = DEFAULT_DECAY_START_DAYS + DISABLED_EXTRA_DAYS
DISABLED_XP = 200
DISABLED_LEVEL = 3

NO_DECAY_START_DAYS = 5
NO_DECAY_INACTIVE_DAYS = NO_DECAY_START_DAYS
NO_DECAY_POINTS_PER_DAY = 9
NO_DECAY_XP = 150
NO_DECAY_LEVEL = 2

DECAY_START_DAYS = 3
DECAY_POINTS_PER_DAY = 12
DECAY_DAYS = 13
DECAY_INACTIVE_DAYS = DECAY_START_DAYS + DECAY_DAYS

LEVEL_THREE = 3
LEVEL_FOUR = 4
LEVEL_FOUR_THRESHOLD = LEVEL_BASE_XP + (LEVEL_FOUR**2) * LEVEL_GROWTH_FACTOR
LEVEL_THREE_THRESHOLD = LEVEL_BASE_XP + (LEVEL_THREE**2) * LEVEL_GROWTH_FACTOR

START_XP_OFFSET = 20
START_XP = LEVEL_FOUR_THRESHOLD - START_XP_OFFSET
DECAY_POINTS = DECAY_POINTS_PER_DAY * DECAY_DAYS
TARGET_XP = START_XP - DECAY_POINTS

LEVEL_START = LEVEL_FOUR
LEVEL_AFTER_DECAY = LEVEL_THREE

ACTIVE_INACTIVE_DAYS = DECAY_START_DAYS
ACTIVE_XP = 220
ACTIVE_LEVEL = 2

EXPECTED_PROCESSED = 2
EXPECTED_UPDATED = 1


class XPDecayTests(TestCase):
    def _create_profile(self, username: str) -> UserProfile:
        user = User.objects.create_user(username=username, password=USER_PASSWORD)
        return UserProfile.objects.get(user=user)

    def test_decay_disabled_skips(self):
        now = timezone.now()
        profile = self._create_profile("xp-decay-disabled")
        profile.xp = DISABLED_XP
        profile.level = DISABLED_LEVEL
        profile.last_activity_at = now - timedelta(days=DISABLED_INACTIVE_DAYS)
        profile.save(update_fields=["xp", "level", "last_activity_at"])

        result = apply_xp_decay(profile=profile, now=now)

        self.assertTrue(result.success)
        self.assertFalse(result.data["changed"])
        self.assertIn(WARNING_DECAY_DISABLED, result.warnings)
        profile.refresh_from_db()
        self.assertEqual(profile.xp, DISABLED_XP)
        self.assertEqual(profile.level, DISABLED_LEVEL)
        self.assertEqual(
            EventLog.objects.filter(event_type=EventLog.EVENT_XP_DECAY).count(),
            0,
        )

    @override_settings(
        ESTUDY_XP_DECAY_ENABLED=True,
        ESTUDY_XP_DECAY_START_DAYS=NO_DECAY_START_DAYS,
        ESTUDY_XP_DECAY_POINTS_PER_DAY=NO_DECAY_POINTS_PER_DAY,
        ESTUDY_XP_DECAY_MIN_XP=DEFAULT_MIN_XP,
        ESTUDY_XP_DECAY_MIN_LEVEL=DEFAULT_MIN_LEVEL,
    )
    def test_decay_skipped_when_inactivity_is_too_short(self):
        now = timezone.now()
        profile = self._create_profile("xp-decay-no-decay")
        profile.xp = NO_DECAY_XP
        profile.level = NO_DECAY_LEVEL
        profile.last_activity_at = now - timedelta(days=NO_DECAY_INACTIVE_DAYS)
        profile.save(update_fields=["xp", "level", "last_activity_at"])

        result = apply_xp_decay(profile=profile, now=now)

        self.assertTrue(result.success)
        self.assertFalse(result.data["changed"])
        self.assertIn(WARNING_NO_DECAY, result.warnings)
        profile.refresh_from_db()
        self.assertEqual(profile.xp, NO_DECAY_XP)
        self.assertEqual(profile.level, NO_DECAY_LEVEL)
        self.assertEqual(
            EventLog.objects.filter(event_type=EventLog.EVENT_XP_DECAY).count(),
            0,
        )

    @override_settings(
        ESTUDY_XP_DECAY_ENABLED=True,
        ESTUDY_XP_DECAY_START_DAYS=DECAY_START_DAYS,
        ESTUDY_XP_DECAY_POINTS_PER_DAY=DECAY_POINTS_PER_DAY,
        ESTUDY_XP_DECAY_MIN_XP=DEFAULT_MIN_XP,
        ESTUDY_XP_DECAY_MIN_LEVEL=DEFAULT_MIN_LEVEL,
    )
    def test_decay_reduces_xp_and_level(self):
        now = timezone.now()
        profile = self._create_profile("xp-decay-applied")
        profile.xp = START_XP
        profile.level = LEVEL_START
        profile.last_activity_at = now - timedelta(days=DECAY_INACTIVE_DAYS)
        profile.save(update_fields=["xp", "level", "last_activity_at"])

        result = apply_xp_decay(profile=profile, now=now)

        self.assertTrue(result.success)
        self.assertTrue(result.data["changed"])
        profile.refresh_from_db()
        self.assertEqual(profile.xp, TARGET_XP)
        self.assertEqual(profile.level, LEVEL_AFTER_DECAY)
        snapshot = result.data["snapshot"]
        self.assertEqual(snapshot.new_xp, TARGET_XP)
        self.assertEqual(snapshot.new_level, LEVEL_AFTER_DECAY)
        self.assertEqual(snapshot.decay_days, DECAY_DAYS)
        self.assertEqual(snapshot.decay_points, DECAY_POINTS)
        self.assertEqual(
            EventLog.objects.filter(event_type=EventLog.EVENT_XP_DECAY).count(),
            1,
        )

    @override_settings(
        ESTUDY_XP_DECAY_ENABLED=True,
        ESTUDY_XP_DECAY_START_DAYS=DECAY_START_DAYS,
        ESTUDY_XP_DECAY_POINTS_PER_DAY=DECAY_POINTS_PER_DAY,
        ESTUDY_XP_DECAY_MIN_XP=DEFAULT_MIN_XP,
        ESTUDY_XP_DECAY_MIN_LEVEL=DEFAULT_MIN_LEVEL,
    )
    def test_run_xp_decay_counts_updates(self):
        now = timezone.now()
        active_profile = self._create_profile("xp-decay-active")
        active_profile.xp = ACTIVE_XP
        active_profile.level = ACTIVE_LEVEL
        active_profile.last_activity_at = now - timedelta(days=ACTIVE_INACTIVE_DAYS)
        active_profile.save(update_fields=["xp", "level", "last_activity_at"])

        inactive_profile = self._create_profile("xp-decay-inactive")
        inactive_profile.xp = START_XP
        inactive_profile.level = LEVEL_START
        inactive_profile.last_activity_at = now - timedelta(days=DECAY_INACTIVE_DAYS)
        inactive_profile.save(update_fields=["xp", "level", "last_activity_at"])

        result = run_xp_decay(now=now)

        self.assertTrue(result.success)
        self.assertEqual(result.data["processed"], EXPECTED_PROCESSED)
        self.assertEqual(result.data["updated"], EXPECTED_UPDATED)
