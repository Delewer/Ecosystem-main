from django.test import TestCase
from django.utils import timezone

from .models import Lesson, Subject
from .services.ai_hallucination_guard import (
    GUARD_SIGNAL_EMPTY,
    GUARD_SIGNAL_FORBIDDEN,
    GUARD_SIGNAL_TOO_LONG,
    GUARD_SIGNAL_UNGROUNDED,
    MAX_HINT_CHARS,
    guard_hint_response,
)

QUESTION_TEXT = "How do loops work?"
FORBIDDEN_ANSWER = "Final answer: just copy the solution."
UNGROUNDED_ANSWER = "Astronomy and cooking tips."
VALID_ANSWER = "Loops repeat a step until a condition is met."

LONG_TOKEN = "loop "
LONG_TOKEN_LENGTH = len(LONG_TOKEN)
LONG_TOKEN_EXTRA = 10


class AIHallucinationGuardTests(TestCase):
    def setUp(self):
        subject = Subject.objects.create(name="CS")
        self.lesson = Lesson.objects.create(
            subject=subject,
            title="Loops",
            content="Lesson content",
            date=timezone.localdate(),
            theory_intro="Loops repeat steps.",
        )

    def test_guard_empty_answer_uses_safe_hint(self):
        result = guard_hint_response(
            question=QUESTION_TEXT,
            answer="",
            lesson=self.lesson,
        )

        self.assertTrue(result.success)
        self.assertTrue(result.data["modified"])
        self.assertIn(GUARD_SIGNAL_EMPTY, result.data["signals"])
        self.assertTrue(result.data["answer"])

    def test_guard_forbidden_answer_replaced(self):
        result = guard_hint_response(
            question=QUESTION_TEXT,
            answer=FORBIDDEN_ANSWER,
            lesson=self.lesson,
        )

        self.assertTrue(result.success)
        self.assertTrue(result.data["modified"])
        self.assertIn(GUARD_SIGNAL_FORBIDDEN, result.data["signals"])
        self.assertNotIn("Final answer", result.data["answer"])

    def test_guard_ungrounded_answer_replaced(self):
        result = guard_hint_response(
            question=QUESTION_TEXT,
            answer=UNGROUNDED_ANSWER,
            lesson=self.lesson,
        )

        self.assertTrue(result.success)
        self.assertTrue(result.data["modified"])
        self.assertIn(GUARD_SIGNAL_UNGROUNDED, result.data["signals"])
        self.assertIn(self.lesson.title, result.data["answer"])

    def test_guard_too_long_truncates(self):
        repeat_count = (MAX_HINT_CHARS // LONG_TOKEN_LENGTH) + LONG_TOKEN_EXTRA
        long_answer = LONG_TOKEN * repeat_count

        result = guard_hint_response(
            question=QUESTION_TEXT,
            answer=long_answer,
            lesson=self.lesson,
        )

        self.assertTrue(result.success)
        self.assertTrue(result.data["modified"])
        self.assertIn(GUARD_SIGNAL_TOO_LONG, result.data["signals"])
        self.assertLessEqual(len(result.data["answer"]), MAX_HINT_CHARS)

    def test_guard_valid_answer_passes(self):
        result = guard_hint_response(
            question=QUESTION_TEXT,
            answer=VALID_ANSWER,
            lesson=self.lesson,
        )

        self.assertTrue(result.success)
        self.assertFalse(result.data["modified"])
        self.assertEqual(result.data["answer"], VALID_ANSWER)
