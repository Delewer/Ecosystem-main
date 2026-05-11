from django.test import TestCase

from .models import Lesson
from .services.lesson_guides import LESSON_GUIDES, MASTERY_PACK_LESSON_SLUGS

MOJIBAKE_PATTERNS = ("В", "Г", "Д", "И", "вЂ", "рџ")
REQUIRED_MASTERY_FIELDS = (
    "goal",
    "worked_example_focus",
    "mistake_repair",
    "mastery_check",
    "next_practice",
)


def _flatten_mastery_text(mastery):
    for field in REQUIRED_MASTERY_FIELDS:
        value = mastery.get(field)
        if isinstance(value, list):
            yield from value
        else:
            yield value


class LessonMasteryPackTests(TestCase):
    def test_first_ten_lessons_have_complete_mastery_contract(self):
        for slug in MASTERY_PACK_LESSON_SLUGS:
            with self.subTest(slug=slug):
                mastery = LESSON_GUIDES.get(slug, {}).get("mastery", {})
                self.assertTrue(mastery)
                for field in REQUIRED_MASTERY_FIELDS:
                    self.assertIn(field, mastery)
                    self.assertTrue(mastery[field])
                self.assertGreaterEqual(len(mastery["mistake_repair"]), 2)
                self.assertLessEqual(len(mastery["mistake_repair"]), 3)

    def test_mastery_pack_text_is_clean_romanian_ascii(self):
        for slug in MASTERY_PACK_LESSON_SLUGS:
            mastery = LESSON_GUIDES[slug]["mastery"]
            for text in _flatten_mastery_text(mastery):
                with self.subTest(slug=slug, text=text):
                    self.assertIsInstance(text, str)
                    text.encode("ascii")
                    for pattern in MOJIBAKE_PATTERNS:
                        self.assertNotIn(pattern, text)

    def test_first_ten_lessons_have_practice_and_tests(self):
        lessons = {
            lesson.slug: lesson
            for lesson in Lesson.objects.filter(slug__in=MASTERY_PACK_LESSON_SLUGS)
        }
        self.assertEqual(set(lessons), set(MASTERY_PACK_LESSON_SLUGS))

        for slug in MASTERY_PACK_LESSON_SLUGS:
            with self.subTest(slug=slug):
                lesson = lessons[slug]
                self.assertTrue(hasattr(lesson, "practice"))
                self.assertTrue(lesson.tests.exists())
