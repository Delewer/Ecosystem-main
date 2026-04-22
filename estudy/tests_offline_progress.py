from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import EventLog, Lesson, LessonProgress, OfflineProgressQueue, Subject
from .services.offline_progress import (
    ACTION_APPLIED,
    ACTION_CONFLICT,
    ACTION_SKIPPED,
    KIND_LESSON_PROGRESS,
    PAYLOAD_COMPLETED,
    PAYLOAD_COMPLETED_AT,
    PAYLOAD_KIND,
    PAYLOAD_POINTS_EARNED,
    PAYLOAD_SECONDS_SPENT,
    apply_offline_progress_entry,
    process_offline_progress_queue,
)

USER_PASSWORD = "pass1234"

POINTS_EARNED = 50
SECONDS_SPENT = 120

EXPECTED_ONE = 1
EXPECTED_ZERO = 0


class OfflineProgressTests(TestCase):
    def _create_user(self, username: str) -> User:
        return User.objects.create_user(username=username, password=USER_PASSWORD)

    def _create_lesson(self) -> Lesson:
        subject = Subject.objects.create(name="Offline")
        return Lesson.objects.create(
            subject=subject,
            title="Offline Lesson",
            content="Content",
            date=timezone.localdate(),
            xp_reward=POINTS_EARNED,
        )

    def test_apply_offline_progress_marks_completed(self):
        user = self._create_user("offline-user")
        lesson = self._create_lesson()
        completed_at = timezone.now() - timedelta(hours=1)
        entry = OfflineProgressQueue.objects.create(
            user=user,
            lesson=lesson,
            payload={
                PAYLOAD_KIND: KIND_LESSON_PROGRESS,
                PAYLOAD_COMPLETED: True,
                PAYLOAD_COMPLETED_AT: completed_at.isoformat(),
                PAYLOAD_POINTS_EARNED: POINTS_EARNED,
                PAYLOAD_SECONDS_SPENT: SECONDS_SPENT,
            },
        )

        result = apply_offline_progress_entry(entry=entry)

        self.assertTrue(result.success)
        snapshot = result.data["snapshot"]
        self.assertEqual(snapshot.action, ACTION_APPLIED)
        progress = LessonProgress.objects.get(user=user, lesson=lesson)
        self.assertTrue(progress.completed)
        self.assertEqual(progress.points_earned, POINTS_EARNED)
        self.assertEqual(progress.fastest_completion_seconds, SECONDS_SPENT)
        entry.refresh_from_db()
        self.assertTrue(entry.synced)
        self.assertEqual(
            EventLog.objects.filter(
                event_type=EventLog.EVENT_OFFLINE_PROGRESS_SYNC
            ).count(),
            EXPECTED_ONE,
        )

    def test_apply_offline_progress_conflict_keeps_server(self):
        user = self._create_user("offline-conflict")
        lesson = self._create_lesson()
        server_time = timezone.now()
        LessonProgress.objects.create(
            user=user,
            lesson=lesson,
            completed=True,
            completed_at=server_time,
        )
        entry = OfflineProgressQueue.objects.create(
            user=user,
            lesson=lesson,
            payload={
                PAYLOAD_KIND: KIND_LESSON_PROGRESS,
                PAYLOAD_COMPLETED: True,
                PAYLOAD_COMPLETED_AT: (server_time - timedelta(days=1)).isoformat(),
            },
        )

        result = apply_offline_progress_entry(entry=entry)

        self.assertTrue(result.success)
        snapshot = result.data["snapshot"]
        self.assertEqual(snapshot.action, ACTION_CONFLICT)
        progress = LessonProgress.objects.get(user=user, lesson=lesson)
        self.assertEqual(progress.completed_at, server_time)
        entry.refresh_from_db()
        self.assertTrue(entry.synced)
        self.assertEqual(
            EventLog.objects.filter(
                event_type=EventLog.EVENT_OFFLINE_PROGRESS_CONFLICT
            ).count(),
            EXPECTED_ONE,
        )

    def test_apply_offline_progress_skips_incomplete(self):
        user = self._create_user("offline-skip")
        lesson = self._create_lesson()
        entry = OfflineProgressQueue.objects.create(
            user=user,
            lesson=lesson,
            payload={
                PAYLOAD_KIND: KIND_LESSON_PROGRESS,
                PAYLOAD_COMPLETED: False,
            },
        )

        result = apply_offline_progress_entry(entry=entry)

        self.assertTrue(result.success)
        snapshot = result.data["snapshot"]
        self.assertEqual(snapshot.action, ACTION_SKIPPED)
        self.assertFalse(
            LessonProgress.objects.filter(user=user, lesson=lesson).exists()
        )
        entry.refresh_from_db()
        self.assertTrue(entry.synced)
        self.assertEqual(EventLog.objects.count(), EXPECTED_ZERO)

    def test_process_offline_progress_queue_counts(self):
        user = self._create_user("offline-batch")
        lesson = self._create_lesson()
        OfflineProgressQueue.objects.create(
            user=user,
            lesson=lesson,
            payload={
                PAYLOAD_KIND: KIND_LESSON_PROGRESS,
                PAYLOAD_COMPLETED: True,
            },
        )
        OfflineProgressQueue.objects.create(
            user=user,
            lesson=lesson,
            payload={"kind": "unknown"},
        )

        result = process_offline_progress_queue()

        self.assertTrue(result.success)
        self.assertEqual(result.data["processed"], 2)
        self.assertEqual(result.data["synced"], 1)
        self.assertEqual(result.data["failed"], 1)
