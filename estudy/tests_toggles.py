from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import Lesson, LessonProgress, Subject
from .services.gamification import (
    build_overall_progress,
    invalidate_overall_progress_cache,
)
from .services.toggles import toggle_lesson_completion_service


class ToggleServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="toggle_tester", password="pw")
        self.subject = Subject.objects.create(name="Sci", description="Science")
        today = timezone.localdate()
        self.lesson = Lesson.objects.create(
            subject=self.subject,
            title="Toggle lesson",
            content="content",
            date=today,
        )

    def test_toggle_marks_completed_and_awards_xp(self):
        res = toggle_lesson_completion_service(self.user, self.lesson)
        self.assertTrue(res["completed"])
        lp = LessonProgress.objects.get(user=self.user, lesson=self.lesson)
        self.assertTrue(lp.completed)
        # xp was awarded via UserProfile.add_xp (exact amount may vary due to missions/badges)
        self.user.refresh_from_db()
        self.assertTrue(hasattr(self.user, "userprofile"))
        self.assertGreater(self.user.userprofile.xp, 0)

    def test_toggle_unmarks(self):
        # mark completed first
        toggle_lesson_completion_service(self.user, self.lesson)
        res2 = toggle_lesson_completion_service(self.user, self.lesson)
        self.assertFalse(res2["completed"])
        lp = LessonProgress.objects.get(user=self.user, lesson=self.lesson)
        self.assertFalse(lp.completed)

    def test_toggle_returns_fresh_snapshot_when_progress_cache_exists(self):
        invalidate_overall_progress_cache(self.user)
        initial = build_overall_progress(self.user)
        self.assertEqual(initial["completed"], 0)

        completed_result = toggle_lesson_completion_service(self.user, self.lesson)
        self.assertEqual(completed_result["progress_snapshot"]["completed"], 1)

        unmarked_result = toggle_lesson_completion_service(self.user, self.lesson)
        self.assertEqual(unmarked_result["progress_snapshot"]["completed"], 0)
