from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import Lesson, LessonComment, Subject
from .services.comment_likes import toggle_comment_like_service
from .services.reputation import COMMENT_LIKE_REWARD

USER_PASSWORD = "pass1234"


class CommentLikesServiceTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username="author", password=USER_PASSWORD
        )
        self.viewer = User.objects.create_user(
            username="viewer", password=USER_PASSWORD
        )
        subject = Subject.objects.create(name="Likes")
        lesson = Lesson.objects.create(
            subject=subject,
            title="Lesson",
            content="Content",
            date=timezone.localdate(),
        )
        self.comment = LessonComment.objects.create(
            lesson=lesson,
            user=self.author,
            content="Great!",
            is_approved=False,
            is_hidden=False,
        )

    def test_toggle_comment_like_updates_reputation(self):
        original_score = self.author.userprofile.reputation_score
        result = toggle_comment_like_service(comment=self.comment, user=self.viewer)

        self.assertTrue(result.success)
        self.assertTrue(result.data["liked"])
        self.author.userprofile.refresh_from_db()
        self.assertEqual(
            self.author.userprofile.reputation_score,
            original_score + COMMENT_LIKE_REWARD,
        )

    def test_toggle_comment_like_removes_reputation(self):
        toggle_comment_like_service(comment=self.comment, user=self.viewer)
        original_score = self.author.userprofile.reputation_score
        result = toggle_comment_like_service(comment=self.comment, user=self.viewer)

        self.assertTrue(result.success)
        self.assertFalse(result.data["liked"])
        self.author.userprofile.refresh_from_db()
        self.assertLess(
            self.author.userprofile.reputation_score,
            original_score,
        )
