from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from inregistrare.models import Profile

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

    def test_mixed_age_tracks_unlock_independently_without_profile_age(self):
        mixed_subject = Subject.objects.create(name="Coding Quest", description="Q")
        today = timezone.localdate()
        older_first = Lesson.objects.create(
            subject=mixed_subject,
            title="Code 1",
            content="c",
            date=today,
            age_bracket=Lesson.AGE_11_13,
        )
        older_second = Lesson.objects.create(
            subject=mixed_subject,
            title="Code 2",
            content="c",
            date=today + timezone.timedelta(days=1),
            age_bracket=Lesson.AGE_11_13,
        )
        junior_first = Lesson.objects.create(
            subject=mixed_subject,
            title="Junior 1",
            content="c",
            date=today,
            age_bracket=Lesson.AGE_8_10,
        )
        junior_second = Lesson.objects.create(
            subject=mixed_subject,
            title="Junior 2",
            content="c",
            date=today + timezone.timedelta(days=1),
            age_bracket=Lesson.AGE_8_10,
        )

        _, accessible_ids, locked_reasons = compute_accessibility(self.user)

        self.assertIn(older_first.id, accessible_ids)
        self.assertIn(junior_first.id, accessible_ids)
        self.assertNotIn(older_second.id, accessible_ids)
        self.assertNotIn(junior_second.id, accessible_ids)
        self.assertEqual(locked_reasons[older_second.id].id, older_first.id)
        self.assertEqual(locked_reasons[junior_second.id].id, junior_first.id)

    def test_profile_age_limits_accessibility_to_matching_track(self):
        mixed_subject = Subject.objects.create(name="Coding Quest", description="Q")
        today = timezone.localdate()
        older_first = Lesson.objects.create(
            subject=mixed_subject,
            title="Code 1",
            content="c",
            date=today,
            age_bracket=Lesson.AGE_11_13,
        )
        older_second = Lesson.objects.create(
            subject=mixed_subject,
            title="Code 2",
            content="c",
            date=today + timezone.timedelta(days=1),
            age_bracket=Lesson.AGE_11_13,
        )
        junior_first = Lesson.objects.create(
            subject=mixed_subject,
            title="Junior 1",
            content="c",
            date=today,
            age_bracket=Lesson.AGE_8_10,
        )
        Profile.objects.update_or_create(
            user=self.user,
            defaults={"email": "access@example.com", "age": 9},
        )

        _, accessible_ids, locked_reasons = compute_accessibility(self.user)

        self.assertIn(junior_first.id, accessible_ids)
        self.assertNotIn(older_first.id, accessible_ids)
        self.assertNotIn(older_second.id, accessible_ids)
        self.assertNotIn(older_first.id, locked_reasons)
