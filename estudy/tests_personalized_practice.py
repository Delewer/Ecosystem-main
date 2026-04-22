from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import CodeExercise, Lesson, Subject, Test, TestAttempt
from .services.personalized_practice import (
    DEFAULT_TASKS_PER_DAY,
    TASK_CODE_EXERCISE,
    TASK_LESSON_REVIEW,
    TASK_QUIZ_RETRY,
    generate_personalized_practice,
)

USER_PASSWORD = "pass1234"
LESSON_CONTENT = "content"

TOTAL_ATTEMPTS = 3


class PersonalizedPracticeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="practice_user", password=USER_PASSWORD
        )
        self.subject = Subject.objects.create(name="Practice Subject")
        self.lesson = Lesson.objects.create(
            subject=self.subject,
            title="Practice Lesson",
            content=LESSON_CONTENT,
            date=timezone.localdate(),
        )
        self.test = Test.objects.create(
            lesson=self.lesson,
            question="Question",
            correct_answer="A",
            wrong_answers=["B", "C"],
        )
        self.exercise = CodeExercise.objects.create(
            lesson=self.lesson,
            title="Practice Exercise",
            description="desc",
            language=CodeExercise.LANG_PYTHON,
        )

    def _add_attempts(self, correct_count: int):
        for idx in range(TOTAL_ATTEMPTS):
            is_correct = idx < correct_count
            TestAttempt.objects.create(
                test=self.test,
                user=self.user,
                selected_answer="A" if is_correct else "B",
                is_correct=is_correct,
            )

    def test_generates_tasks_for_weak_lesson(self):
        self._add_attempts(correct_count=1)

        result = generate_personalized_practice(
            self.user, tasks_per_day=DEFAULT_TASKS_PER_DAY
        )

        self.assertTrue(result.success)
        days = result.data["days"]
        self.assertTrue(days)
        tasks = days[0]["tasks"]

        task_types = {task["task_type"] for task in tasks}
        self.assertIn(TASK_LESSON_REVIEW, task_types)
        self.assertIn(TASK_QUIZ_RETRY, task_types)

    def test_includes_code_exercise_when_slots_available(self):
        self._add_attempts(correct_count=0)

        result = generate_personalized_practice(self.user, tasks_per_day=3)

        self.assertTrue(result.success)
        tasks = result.data["days"][0]["tasks"]
        task_types = {task["task_type"] for task in tasks}
        self.assertIn(TASK_CODE_EXERCISE, task_types)
