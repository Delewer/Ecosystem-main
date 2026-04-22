from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import Lesson, LessonComment, Subject
from .services.reputation import (
    COMMENT_HIDDEN_PENALTY,
    COMMENT_REWARD,
    REPUTATION_MIN,
    TRUSTED_REPUTATION_THRESHOLD,
    WARNING_SELF_LIKE,
    adjust_reputation,
    apply_comment_like_reputation,
    apply_comment_moderation_reputation,
    apply_new_comment_reputation,
)

USER_PASSWORD = "pass1234"


class ReputationServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="rep-user", password=USER_PASSWORD
        )
        self.subject = Subject.objects.create(name="Reputation")
        self.lesson = Lesson.objects.create(
            subject=self.subject,
            title="Lesson",
            content="Content",
            date=timezone.localdate(),
        )

    def _build_comment(self, **kwargs) -> LessonComment:
        return LessonComment(
            lesson=self.lesson,
            user=self.user,
            content="Nice lesson!",
            **kwargs,
        )

    def test_adjust_reputation_updates_score_and_trust(self):
        profile = self.user.userprofile
        result = adjust_reputation(
            user=self.user,
            delta=TRUSTED_REPUTATION_THRESHOLD,
            reason="test",
        )

        profile.refresh_from_db()
        self.assertTrue(result.success)
        self.assertEqual(profile.reputation_score, TRUSTED_REPUTATION_THRESHOLD)
        self.assertTrue(profile.is_trusted_contributor)

    def test_adjust_reputation_clamps_minimum(self):
        result = adjust_reputation(
            user=self.user,
            delta=COMMENT_HIDDEN_PENALTY,
            reason="test",
        )

        profile = self.user.userprofile
        profile.refresh_from_db()
        self.assertTrue(result.success)
        self.assertEqual(profile.reputation_score, REPUTATION_MIN)

    def test_apply_new_comment_reputation_rewards_approved(self):
        comment = self._build_comment(is_approved=True, is_hidden=False)
        result = apply_new_comment_reputation(comment)

        profile = self.user.userprofile
        profile.refresh_from_db()
        self.assertTrue(result.success)
        self.assertEqual(profile.reputation_score, COMMENT_REWARD)

    def test_apply_new_comment_reputation_penalizes_hidden(self):
        comment = self._build_comment(is_approved=False, is_hidden=True)
        result = apply_new_comment_reputation(comment)

        profile = self.user.userprofile
        profile.refresh_from_db()
        self.assertTrue(result.success)
        self.assertEqual(profile.reputation_score, REPUTATION_MIN)
        self.assertEqual(result.data["delta"], COMMENT_HIDDEN_PENALTY)

    def test_apply_comment_moderation_reputation_approve_after_review(self):
        comment = self._build_comment(is_approved=True, is_hidden=False)
        result = apply_comment_moderation_reputation(
            comment=comment,
            previous_state={"is_approved": False, "is_hidden": False},
        )

        profile = self.user.userprofile
        profile.refresh_from_db()
        self.assertTrue(result.success)
        self.assertEqual(profile.reputation_score, COMMENT_REWARD)

    def test_apply_comment_like_reputation_ignores_self_like(self):
        comment = self._build_comment(is_approved=True, is_hidden=False)
        result = apply_comment_like_reputation(
            comment=comment,
            actor=self.user,
            liked=True,
        )

        self.assertTrue(result.success)
        self.assertIn(WARNING_SELF_LIKE, result.warnings)
