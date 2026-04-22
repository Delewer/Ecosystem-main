from django.test import TestCase
from django.utils import timezone

from .models import Lesson, Subject, Test
from .services.code_runner import CodeRunResult
from .services.socratic_followups import (
    CODE_ERROR_QUESTIONS,
    MAX_QUESTIONS,
    build_code_socratic_followups,
    build_test_socratic_followups,
)

LESSON_CONTENT = "content"
SELECTED_ANSWER = "B"
EXPECTED_OUTPUT = "5"
ACTUAL_OUTPUT = "4"
CODE_PASSED = 0
CODE_TOTAL = 1


class SocraticFollowupTests(TestCase):
    def setUp(self):
        self.subject = Subject.objects.create(name="Socratic Subject")
        self.lesson = Lesson.objects.create(
            subject=self.subject,
            title="Socratic Lesson",
            content=LESSON_CONTENT,
            date=timezone.localdate(),
        )
        self.test = Test.objects.create(
            lesson=self.lesson,
            question="Question",
            correct_answer="A",
            wrong_answers=["B", "C"],
            explanation="Review the rule.",
        )

    def test_test_followups_include_selected_answer(self):
        result = build_test_socratic_followups(
            self.test, selected_answer=SELECTED_ANSWER
        )

        self.assertTrue(result.success)
        questions = result.data["questions"]
        self.assertTrue(questions)
        self.assertLessEqual(len(questions), MAX_QUESTIONS)
        self.assertIn(SELECTED_ANSWER, questions[0])

    def test_code_followups_from_error(self):
        result = build_code_socratic_followups(
            CodeRunResult(
                passed=CODE_PASSED,
                total=CODE_TOTAL,
                test_results=[],
                is_correct=False,
                error="SyntaxError: invalid syntax",
            ),
            lesson=self.lesson,
        )

        self.assertTrue(result.success)
        questions = result.data["questions"]
        self.assertTrue(questions)
        self.assertLessEqual(len(questions), MAX_QUESTIONS)
        self.assertEqual(questions[0], CODE_ERROR_QUESTIONS[0])

    def test_code_followups_from_failed_test(self):
        result = build_code_socratic_followups(
            CodeRunResult(
                passed=CODE_PASSED,
                total=CODE_TOTAL,
                test_results=[
                    {
                        "expected": EXPECTED_OUTPUT,
                        "actual": ACTUAL_OUTPUT,
                        "passed": False,
                    }
                ],
                is_correct=False,
                error=None,
            ),
            lesson=self.lesson,
        )

        self.assertTrue(result.success)
        questions = result.data["questions"]
        self.assertTrue(questions)
        self.assertIn(EXPECTED_OUTPUT, questions[0])
        self.assertIn(ACTUAL_OUTPUT, questions[0])
