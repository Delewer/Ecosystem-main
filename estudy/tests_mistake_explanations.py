from django.test import TestCase
from django.utils import timezone

from .models import Lesson, Subject, Test
from .services.code_runner import CodeRunResult
from .services.mistake_explanations import (
    DEFAULT_CODE_EXPLANATION,
    build_code_mistake_explanation,
    build_test_mistake_explanation,
)

LESSON_CONTENT = "content"
TEST_EXPLANATION = "Test explanation."
TEST_EXPECTED = "5"
TEST_ACTUAL = "4"
TEST_DESCRIPTION = "Sample test"

CODE_PASSED = 0
CODE_TOTAL = 1


class MistakeExplanationsTests(TestCase):
    def setUp(self):
        self.subject = Subject.objects.create(name="Explanation Subject")
        self.lesson = Lesson.objects.create(
            subject=self.subject,
            title="Explanation Lesson",
            content=LESSON_CONTENT,
            date=timezone.localdate(),
        )
        self.test = Test.objects.create(
            lesson=self.lesson,
            question="Question",
            correct_answer="A",
            wrong_answers=["B", "C"],
            explanation=TEST_EXPLANATION,
        )

    def test_test_explanation_uses_test_field(self):
        result = build_test_mistake_explanation(self.test, selected_answer="B")

        self.assertTrue(result.success)
        self.assertEqual(
            result.data["explanation"], f"{TEST_EXPLANATION} Your answer: B."
        )

    def test_test_explanation_fallback(self):
        self.test.explanation = ""
        self.test.save(update_fields=["explanation"])
        self.lesson.theory_intro = "Remember the core concept."
        self.lesson.save(update_fields=["theory_intro"])

        result = build_test_mistake_explanation(self.test, selected_answer="C")

        self.assertTrue(result.success)
        self.assertIn("Remember the core concept.", result.data["explanation"])
        self.assertIn("Correct answer", result.data["explanation"])

    def test_code_explanation_from_error(self):
        result = build_code_mistake_explanation(
            CodeRunResult(
                passed=CODE_PASSED,
                total=CODE_TOTAL,
                test_results=[],
                is_correct=False,
                error="SyntaxError: invalid syntax",
            )
        )

        self.assertTrue(result.success)
        self.assertIn("Syntax issue", result.data["explanation"])

    def test_code_explanation_from_failed_test(self):
        result = build_code_mistake_explanation(
            CodeRunResult(
                passed=CODE_PASSED,
                total=CODE_TOTAL,
                test_results=[
                    {
                        "description": TEST_DESCRIPTION,
                        "expected": TEST_EXPECTED,
                        "actual": TEST_ACTUAL,
                        "passed": False,
                        "stderr": "",
                    }
                ],
                is_correct=False,
                error=None,
            )
        )

        self.assertTrue(result.success)
        self.assertIn(TEST_EXPECTED, result.data["explanation"])
        self.assertIn(TEST_ACTUAL, result.data["explanation"])
        self.assertIn(DEFAULT_CODE_EXPLANATION, result.data["explanation"])
