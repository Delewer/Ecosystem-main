from django.contrib.auth.models import User
from django.test import TestCase

from .models import (
    CommunityCuratedAnswer,
    CommunityReply,
    CommunityThread,
    EventLog,
    UserProfile,
)
from .services.curated_answers import (
    ERROR_NOT_ALLOWED,
    ERROR_THREAD_MISMATCH,
    WARNING_ALREADY_CURATED,
    WARNING_NOT_CURATED,
    curate_reply,
    remove_curated_reply,
)

USER_PASSWORD = "pass1234"

EXPECTED_ZERO = 0
EXPECTED_ONE = 1
EXPECTED_TWO = 2


class CuratedAnswersTests(TestCase):
    def _create_user(self, username: str, role: str) -> User:
        user = User.objects.create_user(username=username, password=USER_PASSWORD)
        profile = user.userprofile
        profile.status = role
        profile.save(update_fields=["status"])
        return user

    def _create_thread(self, author: User, title_suffix: str) -> CommunityThread:
        return CommunityThread.objects.create(
            title=f"Thread {title_suffix}",
            body="Body",
            author=author,
        )

    def _create_reply(self, author: User, thread: CommunityThread) -> CommunityReply:
        return CommunityReply.objects.create(
            thread=thread,
            author=author,
            body="Reply body",
        )

    def test_curate_reply_requires_teacher(self):
        student = self._create_user("student", UserProfile.ROLE_STUDENT)
        thread = self._create_thread(student, "A")
        reply = self._create_reply(student, thread)

        result = curate_reply(thread=thread, reply=reply, curator=student)

        self.assertFalse(result.success)
        self.assertEqual(result.error, ERROR_NOT_ALLOWED)
        self.assertEqual(CommunityCuratedAnswer.objects.count(), EXPECTED_ZERO)
        self.assertEqual(
            EventLog.objects.filter(
                event_type=EventLog.EVENT_COMMUNITY_CURATION
            ).count(),
            EXPECTED_ZERO,
        )

    def test_curate_reply_creates_record(self):
        teacher = self._create_user("teacher", UserProfile.ROLE_PROFESSOR)
        student = self._create_user("author", UserProfile.ROLE_STUDENT)
        thread = self._create_thread(student, "B")
        reply = self._create_reply(student, thread)

        result = curate_reply(thread=thread, reply=reply, curator=teacher)

        self.assertTrue(result.success)
        self.assertTrue(result.data["created"])
        curated = CommunityCuratedAnswer.objects.get(reply=reply)
        self.assertEqual(curated.thread_id, thread.id)
        self.assertEqual(curated.curated_by_id, teacher.id)
        self.assertEqual(
            EventLog.objects.filter(
                event_type=EventLog.EVENT_COMMUNITY_CURATION
            ).count(),
            EXPECTED_ONE,
        )

    def test_curate_reply_thread_mismatch(self):
        teacher = self._create_user("teacher2", UserProfile.ROLE_PROFESSOR)
        student = self._create_user("author2", UserProfile.ROLE_STUDENT)
        thread_a = self._create_thread(student, "C")
        thread_b = self._create_thread(student, "D")
        reply = self._create_reply(student, thread_b)

        result = curate_reply(thread=thread_a, reply=reply, curator=teacher)

        self.assertFalse(result.success)
        self.assertEqual(result.error, ERROR_THREAD_MISMATCH)
        self.assertEqual(CommunityCuratedAnswer.objects.count(), EXPECTED_ZERO)

    def test_curate_reply_twice_warns(self):
        teacher = self._create_user("teacher3", UserProfile.ROLE_PROFESSOR)
        student = self._create_user("author3", UserProfile.ROLE_STUDENT)
        thread = self._create_thread(student, "E")
        reply = self._create_reply(student, thread)

        first = curate_reply(thread=thread, reply=reply, curator=teacher)
        second = curate_reply(thread=thread, reply=reply, curator=teacher)

        self.assertTrue(first.success)
        self.assertTrue(second.success)
        self.assertIn(WARNING_ALREADY_CURATED, second.warnings)
        self.assertEqual(CommunityCuratedAnswer.objects.count(), EXPECTED_ONE)

    def test_remove_curated_reply(self):
        teacher = self._create_user("teacher4", UserProfile.ROLE_PROFESSOR)
        student = self._create_user("author4", UserProfile.ROLE_STUDENT)
        thread = self._create_thread(student, "F")
        reply = self._create_reply(student, thread)

        curate_reply(thread=thread, reply=reply, curator=teacher)
        result = remove_curated_reply(thread=thread, reply=reply, curator=teacher)

        self.assertTrue(result.success)
        self.assertTrue(result.data["removed"])
        self.assertEqual(CommunityCuratedAnswer.objects.count(), EXPECTED_ZERO)
        self.assertEqual(
            EventLog.objects.filter(
                event_type=EventLog.EVENT_COMMUNITY_CURATION
            ).count(),
            EXPECTED_TWO,
        )

    def test_remove_curated_reply_missing(self):
        teacher = self._create_user("teacher5", UserProfile.ROLE_PROFESSOR)
        student = self._create_user("author5", UserProfile.ROLE_STUDENT)
        thread = self._create_thread(student, "G")
        reply = self._create_reply(student, thread)

        result = remove_curated_reply(thread=thread, reply=reply, curator=teacher)

        self.assertTrue(result.success)
        self.assertFalse(result.data["removed"])
        self.assertIn(WARNING_NOT_CURATED, result.warnings)
        self.assertEqual(CommunityCuratedAnswer.objects.count(), EXPECTED_ZERO)
