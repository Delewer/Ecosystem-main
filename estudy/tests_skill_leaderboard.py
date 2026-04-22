from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import Lesson, LessonProgress, Skill, Subject
from .services.skill_leaderboard import (
    LIMIT_CLAMP_WARNING,
    MAX_LIMIT,
    build_skill_leaderboard,
)

USER_ONE = "user_one"
USER_TWO = "user_two"
USER_PASSWORD = "pass1234"

POINTS_FIRST = 80
POINTS_SECOND = 40
POINTS_OTHER = 70
EXPECTED_COUNT = 2

LIMIT_OVERFLOW = 1


class SkillLeaderboardTests(TestCase):
    def setUp(self):
        self.subject = Subject.objects.create(name="Skill Subject")
        self.skill = Skill.objects.create(
            slug="loop-skill",
            title="Loops",
        )
        self.lesson_one = Lesson.objects.create(
            subject=self.subject,
            title="Lesson One",
            content="Content",
            date=timezone.localdate(),
        )
        self.lesson_two = Lesson.objects.create(
            subject=self.subject,
            title="Lesson Two",
            content="Content",
            date=timezone.localdate(),
        )
        self.lesson_one.skills.add(self.skill)
        self.lesson_two.skills.add(self.skill)

    def test_build_skill_leaderboard_orders_by_points(self):
        user_one = User.objects.create_user(username=USER_ONE, password=USER_PASSWORD)
        user_two = User.objects.create_user(username=USER_TWO, password=USER_PASSWORD)

        LessonProgress.objects.create(
            user=user_one,
            lesson=self.lesson_one,
            completed=True,
            points_earned=POINTS_FIRST,
        )
        LessonProgress.objects.create(
            user=user_one,
            lesson=self.lesson_two,
            completed=True,
            points_earned=POINTS_SECOND,
        )
        LessonProgress.objects.create(
            user=user_two,
            lesson=self.lesson_one,
            completed=True,
            points_earned=POINTS_OTHER,
        )

        result = build_skill_leaderboard(skill_slug=self.skill.slug)

        self.assertTrue(result.success)
        entries = result.data["entries"]
        self.assertEqual(len(entries), EXPECTED_COUNT)
        self.assertEqual(entries[0]["username"], USER_ONE)
        self.assertEqual(entries[0]["score"], POINTS_FIRST + POINTS_SECOND)
        self.assertEqual(entries[0]["lessons_completed"], EXPECTED_COUNT)
        self.assertEqual(entries[1]["username"], USER_TWO)
        self.assertEqual(entries[1]["score"], POINTS_OTHER)

    def test_build_skill_leaderboard_requires_skill(self):
        result = build_skill_leaderboard()

        self.assertFalse(result.success)

    def test_build_skill_leaderboard_unknown_skill(self):
        result = build_skill_leaderboard(skill_slug="missing-skill")

        self.assertFalse(result.success)

    def test_build_skill_leaderboard_limit_clamped(self):
        user_one = User.objects.create_user(username=USER_ONE, password=USER_PASSWORD)
        LessonProgress.objects.create(
            user=user_one,
            lesson=self.lesson_one,
            completed=True,
            points_earned=POINTS_FIRST,
        )

        result = build_skill_leaderboard(
            skill_slug=self.skill.slug,
            limit=MAX_LIMIT + LIMIT_OVERFLOW,
        )

        self.assertTrue(result.success)
        self.assertIn(LIMIT_CLAMP_WARNING, result.warnings)
