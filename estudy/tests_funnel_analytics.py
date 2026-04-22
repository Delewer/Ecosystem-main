from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import EventLog
from .services.funnel_analytics import PERCENT_MAX, SCORE_DECIMALS, build_event_funnel

USER_PASSWORD = "pass1234"

STEP_ONE_COUNT = 3
STEP_TWO_COUNT = 2
STEP_THREE_COUNT = 1
STEP_FOUR_COUNT = 1

ORDERED_STEP_ONE_COUNT = 3
ORDERED_STEP_TWO_COUNT = 1


class FunnelAnalyticsTests(TestCase):
    def _create_event(self, user, event_type, created_at=None):
        event = EventLog.objects.create(user=user, event_type=event_type)
        if created_at is not None:
            EventLog.objects.filter(pk=event.pk).update(created_at=created_at)
        return event

    def test_event_funnel_unordered(self):
        user_one = User.objects.create_user(username="u1", password=USER_PASSWORD)
        user_two = User.objects.create_user(username="u2", password=USER_PASSWORD)
        user_three = User.objects.create_user(username="u3", password=USER_PASSWORD)

        self._create_event(user_one, EventLog.EVENT_LOGIN)
        self._create_event(user_one, EventLog.EVENT_LESSON_VIEW)
        self._create_event(user_one, EventLog.EVENT_TEST_START)
        self._create_event(user_one, EventLog.EVENT_TEST_SUBMIT)

        self._create_event(user_two, EventLog.EVENT_LOGIN)
        self._create_event(user_two, EventLog.EVENT_LESSON_VIEW)

        self._create_event(user_three, EventLog.EVENT_LOGIN)

        self._create_event(None, EventLog.EVENT_LESSON_VIEW)

        result = build_event_funnel(
            [
                EventLog.EVENT_LOGIN,
                EventLog.EVENT_LESSON_VIEW,
                EventLog.EVENT_TEST_START,
                EventLog.EVENT_TEST_SUBMIT,
            ]
        )

        self.assertTrue(result.success)
        snapshots = result.data["snapshots"]
        counts = [snapshot.user_count for snapshot in snapshots]
        self.assertEqual(
            counts,
            [
                STEP_ONE_COUNT,
                STEP_TWO_COUNT,
                STEP_THREE_COUNT,
                STEP_FOUR_COUNT,
            ],
        )

        expected_step2 = round(
            (STEP_TWO_COUNT / STEP_ONE_COUNT) * PERCENT_MAX, SCORE_DECIMALS
        )
        expected_step3 = round(
            (STEP_THREE_COUNT / STEP_TWO_COUNT) * PERCENT_MAX, SCORE_DECIMALS
        )
        expected_step4 = round(
            (STEP_FOUR_COUNT / STEP_THREE_COUNT) * PERCENT_MAX, SCORE_DECIMALS
        )

        self.assertEqual(snapshots[0].conversion_rate, PERCENT_MAX)
        self.assertEqual(snapshots[1].conversion_rate, expected_step2)
        self.assertEqual(snapshots[2].conversion_rate, expected_step3)
        self.assertEqual(snapshots[3].conversion_rate, expected_step4)

        summary = result.data["summary"]
        expected_overall = round(
            (STEP_FOUR_COUNT / STEP_ONE_COUNT) * PERCENT_MAX, SCORE_DECIMALS
        )
        self.assertEqual(summary["overall_conversion_rate"], expected_overall)

    def test_event_funnel_ordered(self):
        user_one = User.objects.create_user(username="u4", password=USER_PASSWORD)
        user_two = User.objects.create_user(username="u5", password=USER_PASSWORD)
        user_three = User.objects.create_user(username="u6", password=USER_PASSWORD)

        base_time = timezone.now()

        self._create_event(user_one, EventLog.EVENT_LOGIN, created_at=base_time)
        self._create_event(
            user_one,
            EventLog.EVENT_LESSON_VIEW,
            created_at=base_time + timedelta(minutes=1),
        )

        self._create_event(
            user_two,
            EventLog.EVENT_LESSON_VIEW,
            created_at=base_time,
        )
        self._create_event(
            user_two,
            EventLog.EVENT_LOGIN,
            created_at=base_time + timedelta(minutes=1),
        )

        self._create_event(user_three, EventLog.EVENT_LOGIN, created_at=base_time)

        result = build_event_funnel(
            [EventLog.EVENT_LOGIN, EventLog.EVENT_LESSON_VIEW],
            require_order=True,
        )

        self.assertTrue(result.success)
        snapshots = result.data["snapshots"]
        counts = [snapshot.user_count for snapshot in snapshots]
        self.assertEqual(counts, [ORDERED_STEP_ONE_COUNT, ORDERED_STEP_TWO_COUNT])
        expected_step2 = round(
            (ORDERED_STEP_TWO_COUNT / ORDERED_STEP_ONE_COUNT) * PERCENT_MAX,
            SCORE_DECIMALS,
        )
        self.assertEqual(snapshots[1].conversion_rate, expected_step2)
