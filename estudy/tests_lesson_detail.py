from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from inregistrare.models import Profile

from .models import Lesson, LessonProgress, Subject
from .services.lesson_detail import BlockingLessonRequired, prepare_lesson_detail


class LessonDetailServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ld", password="pw")
        self.subject = Subject.objects.create(name="S", description="D")
        today = timezone.localdate()
        self.l1 = Lesson.objects.create(
            subject=self.subject, title="L1", content="c", date=today
        )
        self.l2 = Lesson.objects.create(
            subject=self.subject, title="L2", content="c", date=today
        )
        self.l3 = Lesson.objects.create(
            subject=self.subject, title="L3", content="c", date=today
        )

    def test_blocking_lesson_raises(self):
        # when accessing l2 without completing l1, expect BlockingLessonRequired
        with self.assertRaises(BlockingLessonRequired) as cm:
            prepare_lesson_detail(self.user, self.l2.slug)
        self.assertEqual(cm.exception.blocking_slug, self.l1.slug)

    def test_payload_when_no_block(self):
        # complete l1 then fetch l2
        LessonProgress.objects.create(user=self.user, lesson=self.l1, completed=True)
        payload = prepare_lesson_detail(self.user, self.l2.slug)
        self.assertIn("lesson", payload)
        self.assertIn("subject_sequence", payload)
        self.assertIn("lesson_position", payload)
        self.assertEqual(payload["lesson"].slug, self.l2.slug)

    def test_next_lesson_locked_until_current_is_completed(self):
        LessonProgress.objects.create(user=self.user, lesson=self.l1, completed=True)

        payload_before = prepare_lesson_detail(self.user, self.l2.slug)
        self.assertTrue(payload_before["next_locked"])
        self.assertIsNone(payload_before["progress"])

        LessonProgress.objects.create(user=self.user, lesson=self.l2, completed=True)
        payload_after = prepare_lesson_detail(self.user, self.l2.slug)
        self.assertFalse(payload_after["next_locked"])
        self.assertIsNotNone(payload_after["progress"])
        self.assertTrue(payload_after["progress"].completed)

    def test_subject_sequence_marks_second_lesson_accessible_after_first_completion(
        self,
    ):
        LessonProgress.objects.create(user=self.user, lesson=self.l1, completed=True)
        payload = prepare_lesson_detail(self.user, self.l2.slug)
        sequence = {item["lesson"].id: item for item in payload["subject_sequence"]}
        self.assertTrue(sequence[self.l2.id]["accessible"])
        self.assertFalse(sequence[self.l3.id]["accessible"])

    def test_lesson_mode_switches_from_intro_to_code_arena(self):
        LessonProgress.objects.create(user=self.user, lesson=self.l1, completed=True)
        intro_payload = prepare_lesson_detail(self.user, self.l2.slug)
        self.assertTrue(intro_payload["is_intro_lesson"])
        self.assertGreaterEqual(len(intro_payload["mentor_characters"]), 3)
        self.assertTrue(intro_payload["code_arena_steps"])

        LessonProgress.objects.create(user=self.user, lesson=self.l2, completed=True)
        arena_payload = prepare_lesson_detail(self.user, self.l3.slug)
        self.assertFalse(arena_payload["is_intro_lesson"])
        self.assertTrue(arena_payload["code_arena_steps"])

    def test_payload_filters_cyrillic_display_fields(self):
        self.l1.theory_intro = "Сегодня изучаем переменные."
        self.l1.story_anchor = "Сегодня мы исследуем тему."
        self.l1.content_tracks = ["Основной маршрут", "Бонус"]
        self.l1.content = "Текст на русском."
        self.l1.save()

        payload = prepare_lesson_detail(self.user, self.l1.slug)

        self.assertNotIn("Сегодня", payload["lesson_intro_text"])
        self.assertEqual(payload["lesson_story_anchor"], "")
        self.assertTrue(payload["lesson_track_items"])
        self.assertNotIn("Основной", " ".join(payload["lesson_track_items"]))
        self.assertNotIn("Текст", payload["lesson_content_text"])

    def test_junior_python_track_uses_visual_mode_without_robot_lab(self):
        self.subject.name = "Coding Quest"
        self.subject.save(update_fields=["name"])
        self.l1.age_bracket = Lesson.AGE_8_10
        self.l1.save(update_fields=["age_bracket"])

        payload = prepare_lesson_detail(self.user, self.l1.slug)

        self.assertTrue(payload["is_python_track"])
        self.assertTrue(payload["is_junior_track"])
        self.assertFalse(payload["show_robot_lab_preview"])
        self.assertFalse(payload["show_full_code_lab"])
        self.assertEqual(payload["example_nav_label"], "Puzzle")
        self.assertEqual(payload["practice_section_title"], "Puzzle si potriviri")
        self.assertFalse(payload["show_guided_code_snippet"])
        self.assertIn("order", payload["junior_games"])
        self.assertIn("colors", payload["junior_games"])
        self.assertIn("memory", payload["junior_games"])

    def test_older_python_track_enables_robot_lab_code_mode(self):
        self.subject.name = "Coding Quest"
        self.subject.save(update_fields=["name"])
        self.l1.age_bracket = Lesson.AGE_11_13
        self.l1.save(update_fields=["age_bracket"])

        payload = prepare_lesson_detail(self.user, self.l1.slug)

        self.assertTrue(payload["is_python_track"])
        self.assertFalse(payload["is_junior_track"])
        self.assertTrue(payload["show_robot_lab_preview"])
        self.assertTrue(payload["show_full_code_lab"])
        self.assertTrue(payload["show_robot_lab_cta"])
        self.assertEqual(payload["example_nav_label"], "Robot Lab")
        self.assertTrue(payload["show_guided_code_snippet"])

    def test_profile_age_can_force_junior_mode_for_python_lesson(self):
        self.subject.name = "Coding Quest"
        self.subject.save(update_fields=["name"])
        self.l1.age_bracket = Lesson.AGE_11_13
        self.l1.save(update_fields=["age_bracket"])
        Profile.objects.update_or_create(
            user=self.user,
            defaults={"email": "ld@example.com", "age": 9},
        )

        payload = prepare_lesson_detail(self.user, self.l1.slug)

        self.assertTrue(payload["is_junior_track"])
        self.assertFalse(payload["show_robot_lab_preview"])
        self.assertEqual(payload["age_mode_source"], "profile")
        self.assertEqual(payload["learner_age"], 9)

    def test_profile_age_can_force_code_mode_for_python_lesson(self):
        self.subject.name = "Coding Quest"
        self.subject.save(update_fields=["name"])
        self.l1.age_bracket = Lesson.AGE_8_10
        self.l1.save(update_fields=["age_bracket"])
        Profile.objects.update_or_create(
            user=self.user,
            defaults={"email": "ld@example.com", "age": 12},
        )

        payload = prepare_lesson_detail(self.user, self.l1.slug)

        self.assertFalse(payload["is_junior_track"])
        self.assertTrue(payload["show_robot_lab_preview"])
        self.assertTrue(payload["show_full_code_lab"])
        self.assertEqual(payload["age_mode_source"], "profile")
        self.assertEqual(payload["learner_age"], 12)
