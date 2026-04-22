from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import Lesson, LessonProgress, Subject
from .services.lesson_access import compute_accessibility


class LessonAccessibilityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="access", password="pw")
        self.subject = Subject.objects.create(name="Algorithms", description="S")
        today = timezone.localdate()
        self.l1 = Lesson.objects.create(
            subject=self.subject, title="A1", content="c", date=today
        )
        self.l2 = Lesson.objects.create(
            subject=self.subject, title="A2", content="c", date=today
        )
        self.l3 = Lesson.objects.create(
            subject=self.subject, title="A3", content="c", date=today
        )

    def test_only_first_incomplete_lesson_is_accessible(self):
        _, accessible_ids, locked_reasons = compute_accessibility(self.user)
        self.assertIn(self.l1.id, accessible_ids)
        self.assertNotIn(self.l2.id, accessible_ids)
        self.assertEqual(locked_reasons[self.l2.id].id, self.l1.id)
        self.assertEqual(locked_reasons[self.l3.id].id, self.l1.id)

    def test_next_lesson_unlocks_after_previous_completion(self):
        LessonProgress.objects.create(user=self.user, lesson=self.l1, completed=True)
        completed_ids, accessible_ids, locked_reasons = compute_accessibility(self.user)
        self.assertIn(self.l1.id, completed_ids)
        self.assertIn(self.l2.id, accessible_ids)
        self.assertNotIn(self.l3.id, accessible_ids)
        self.assertEqual(locked_reasons[self.l3.id].id, self.l2.id)
