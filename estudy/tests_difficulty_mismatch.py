from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import Lesson, Subject, Test, TestAttempt
from .services.difficulty_mismatch import (
    INSUFFICIENT_DATA_WARNING,
    PERCENT_MAX,
    RECOMMEND_HIGHER,
    RECOMMEND_LOWER,
    RECOMMEND_MATCH,
    SCORE_DECIMALS,
    build_lesson_difficulty_analysis,
    find_difficulty_mismatches,
)

USER_PASSWORD = "pass1234"
LESSON_CONTENT = "content"

TOTAL_ATTEMPTS = 4
CORRECT_ALL = 4
CORRECT_NONE = 0

TIME_ONE_MS = 2000
TIME_TWO_MS = 4000


class DifficultyMismatchTests(TestCase):
    def setUp(self):
        self.subject = Subject.objects.create(name="Mismatch Subject")

    def _create_lesson_with_test(self, title, difficulty):
        lesson = Lesson.objects.create(
            subject=self.subject,
            title=title,
            content=LESSON_CONTENT,
            date=timezone.localdate(),
            difficulty=difficulty,
        )
        test = Test.objects.create(
            lesson=lesson,
            question="Question",
            correct_answer="A",
            wrong_answers=["B", "C"],
        )
        return lesson, test

    def _create_attempt(self, user, test, is_correct, time_taken_ms):
        return TestAttempt.objects.create(
            test=test,
            user=user,
            selected_answer="A" if is_correct else "B",
            is_correct=is_correct,
            time_taken_ms=time_taken_ms,
        )

    def test_insufficient_data_warning(self):
        lesson, _ = self._create_lesson_with_test(
            "Mismatch Lesson", Lesson.DIFFICULTY_BEGINNER
        )

        result = build_lesson_difficulty_analysis(lesson)

        self.assertTrue(result.success)
        self.assertIn(INSUFFICIENT_DATA_WARNING, result.warnings)
        self.assertTrue(result.data["analysis"]["insufficient_data"])

    def test_match_recommendation(self):
        lesson, test = self._create_lesson_with_test(
            "Match Lesson", Lesson.DIFFICULTY_BEGINNER
        )
        for idx in range(TOTAL_ATTEMPTS):
            user = User.objects.create_user(
                username=f"match_{idx}", password=USER_PASSWORD
            )
            self._create_attempt(user, test, True, TIME_ONE_MS)

        result = build_lesson_difficulty_analysis(lesson)
        analysis = result.data["analysis"]

        expected_success = round(
            (CORRECT_ALL / TOTAL_ATTEMPTS) * PERCENT_MAX, SCORE_DECIMALS
        )

        self.assertTrue(result.success)
        self.assertTrue(analysis["difficulty_match"])
        self.assertEqual(analysis["real_difficulty"], Lesson.DIFFICULTY_BEGINNER)
        self.assertEqual(analysis["success_rate"], expected_success)
        self.assertEqual(analysis["recommendation"], RECOMMEND_MATCH)

    def test_mismatch_recommendation(self):
        lesson, test = self._create_lesson_with_test(
            "Mismatch Lesson 2", Lesson.DIFFICULTY_BEGINNER
        )
        for idx in range(TOTAL_ATTEMPTS):
            user = User.objects.create_user(
                username=f"mismatch_{idx}", password=USER_PASSWORD
            )
            time_taken = TIME_ONE_MS if idx % 2 == 0 else TIME_TWO_MS
            self._create_attempt(user, test, False, time_taken)

        result = build_lesson_difficulty_analysis(lesson)
        analysis = result.data["analysis"]

        expected_success = round(
            (CORRECT_NONE / TOTAL_ATTEMPTS) * PERCENT_MAX, SCORE_DECIMALS
        )

        self.assertTrue(result.success)
        self.assertFalse(analysis["difficulty_match"])
        self.assertEqual(analysis["real_difficulty"], Lesson.DIFFICULTY_ADVANCED)
        self.assertEqual(analysis["success_rate"], expected_success)
        self.assertEqual(analysis["recommendation"], RECOMMEND_HIGHER)

    def test_lower_recommendation(self):
        lesson, test = self._create_lesson_with_test(
            "Lower Lesson", Lesson.DIFFICULTY_ADVANCED
        )
        for idx in range(TOTAL_ATTEMPTS):
            user = User.objects.create_user(
                username=f"lower_{idx}", password=USER_PASSWORD
            )
            self._create_attempt(user, test, True, TIME_ONE_MS)

        result = build_lesson_difficulty_analysis(lesson)
        analysis = result.data["analysis"]

        self.assertTrue(result.success)
        self.assertEqual(analysis["real_difficulty"], Lesson.DIFFICULTY_BEGINNER)
        self.assertEqual(analysis["recommendation"], RECOMMEND_LOWER)

    def test_find_difficulty_mismatches(self):
        mismatched_lesson, mismatched_test = self._create_lesson_with_test(
            "Mismatch Scan", Lesson.DIFFICULTY_BEGINNER
        )
        matched_lesson, matched_test = self._create_lesson_with_test(
            "Match Scan", Lesson.DIFFICULTY_BEGINNER
        )

        for idx in range(TOTAL_ATTEMPTS):
            user = User.objects.create_user(
                username=f"scan_{idx}", password=USER_PASSWORD
            )
            self._create_attempt(user, mismatched_test, False, TIME_ONE_MS)
            self._create_attempt(user, matched_test, True, TIME_ONE_MS)

        result = find_difficulty_mismatches()

        self.assertTrue(result.success)
        self.assertEqual(result.data["checked"], 2)
        self.assertEqual(result.data["insufficient"], 0)
        self.assertEqual(len(result.data["mismatches"]), 1)
        self.assertEqual(
            result.data["mismatches"][0]["lesson"], mismatched_lesson.title
        )
