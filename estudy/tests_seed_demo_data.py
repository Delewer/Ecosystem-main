from django.test import TestCase

from .models import (
    CodeExercise,
    Course,
    CourseGoal,
    LearningPath,
    LearningPathLesson,
    Lesson,
    Module,
    Subject,
    Test,
    TopicTag,
)
from .services.seed_demo_data import seed_demo_data

MIN_EXPECTED_COUNT = 1
ZERO_COUNT = 0


class SeedDemoDataTests(TestCase):
    def test_seed_creates_demo_content(self):
        result = seed_demo_data()

        expected_models = {
            "subjects": Subject,
            "courses": Course,
            "course_goals": CourseGoal,
            "modules": Module,
            "lessons": Lesson,
            "topic_tags": TopicTag,
            "tests": Test,
            "code_exercises": CodeExercise,
            "learning_paths": LearningPath,
            "learning_path_lessons": LearningPathLesson,
        }

        for key, model in expected_models.items():
            count = model.objects.count()
            self.assertGreaterEqual(count, MIN_EXPECTED_COUNT)
            self.assertEqual(result.totals[key], count)

    def test_seed_is_idempotent(self):
        seed_demo_data()
        expected_models = {
            "subjects": Subject,
            "courses": Course,
            "course_goals": CourseGoal,
            "modules": Module,
            "lessons": Lesson,
            "topic_tags": TopicTag,
            "tests": Test,
            "code_exercises": CodeExercise,
            "learning_paths": LearningPath,
            "learning_path_lessons": LearningPathLesson,
        }
        counts_before = {
            key: model.objects.count() for key, model in expected_models.items()
        }

        result = seed_demo_data()
        counts_after = {
            key: model.objects.count() for key, model in expected_models.items()
        }

        self.assertEqual(counts_before, counts_after)
        for key, created_count in result.created.items():
            self.assertEqual(created_count, ZERO_COUNT, msg=f"Expected no new {key}")
