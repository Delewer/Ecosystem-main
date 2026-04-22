from django.test import TestCase
from django.utils import timezone

from .models import Lesson, Subject
from .services.ai_context import MAX_CLUES, build_lesson_clues

TAKEAWAYS = [
    "first",
    "second",
    "third",
    "fourth",
    "fifth",
]


class AIContextTests(TestCase):
    def test_build_lesson_clues_limits_output(self):
        subject = Subject.objects.create(name="Context")
        lesson = Lesson.objects.create(
            subject=subject,
            title="Lesson",
            content="Content",
            date=timezone.localdate(),
            theory_takeaways=TAKEAWAYS,
        )

        clues = build_lesson_clues(lesson)

        self.assertEqual(len(clues), MAX_CLUES)
        self.assertEqual(clues, TAKEAWAYS[:MAX_CLUES])

    def test_build_lesson_clues_empty_lesson(self):
        self.assertEqual(build_lesson_clues(None), [])
