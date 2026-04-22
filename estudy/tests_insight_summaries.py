from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import (
    Classroom,
    ClassroomMembership,
    Lesson,
    LessonProgress,
    ParentChildLink,
    Subject,
    Test,
    TestAttempt,
)
from .services.insight_summaries import (
    CONCERN_LOW_COMPLETION,
    CONCERN_LOW_SCORE,
    CONCERN_NO_STREAK,
    INSIGHT_LOW_ACTIVITY,
    INSIGHT_LOW_SUBMISSION,
    INSIGHT_LOW_SUCCESS,
    INSIGHT_RISK_ALERTS,
    build_parent_progress_summary,
    build_teacher_insights_summary,
)

USER_PASSWORD = "pass1234"
LESSON_CONTENT = "content"
LOW_SCORE = 20
ZERO_STREAK = 0


class InsightSummariesTests(TestCase):
    def setUp(self):
        self.subject = Subject.objects.create(name="Insight Subject")
        self.lesson_one = Lesson.objects.create(
            subject=self.subject,
            title="Insight Lesson 1",
            content=LESSON_CONTENT,
            date=timezone.localdate(),
        )
        self.lesson_two = Lesson.objects.create(
            subject=self.subject,
            title="Insight Lesson 2",
            content=LESSON_CONTENT,
            date=timezone.localdate(),
        )
        self.test = Test.objects.create(
            lesson=self.lesson_one,
            question="What is insight?",
            correct_answer="A",
            wrong_answers=["B", "C"],
        )

    def test_teacher_insights_summary_flags_issues(self):
        teacher = User.objects.create_user(username="teacher", password=USER_PASSWORD)
        classroom = Classroom.objects.create(name="Insight Class", owner=teacher)
        student = User.objects.create_user(username="student", password=USER_PASSWORD)
        ClassroomMembership.objects.create(
            classroom=classroom,
            user=student,
            role=ClassroomMembership.ROLE_STUDENT,
            approved=True,
        )
        TestAttempt.objects.create(
            test=self.test,
            user=student,
            selected_answer="B",
            is_correct=False,
            awarded_points=LOW_SCORE,
        )

        result = build_teacher_insights_summary(classroom)

        self.assertTrue(result.success)
        codes = {item["code"] for item in result.data["insights"]}
        self.assertIn(INSIGHT_LOW_ACTIVITY, codes)
        self.assertIn(INSIGHT_LOW_SUCCESS, codes)
        self.assertIn(INSIGHT_LOW_SUBMISSION, codes)
        self.assertIn(INSIGHT_RISK_ALERTS, codes)

    def test_parent_progress_summary_requires_link(self):
        parent = User.objects.create_user(username="parent", password=USER_PASSWORD)
        child = User.objects.create_user(username="child", password=USER_PASSWORD)

        result = build_parent_progress_summary(parent, child)

        self.assertFalse(result.success)

    def test_parent_progress_summary_reports_concerns(self):
        parent = User.objects.create_user(username="parent2", password=USER_PASSWORD)
        child = User.objects.create_user(username="child2", password=USER_PASSWORD)
        ParentChildLink.objects.create(parent=parent, child=child, approved=True)

        LessonProgress.objects.create(
            user=child, lesson=self.lesson_one, completed=False
        )
        TestAttempt.objects.create(
            test=self.test,
            user=child,
            selected_answer="B",
            is_correct=False,
            awarded_points=LOW_SCORE,
        )
        child.userprofile.streak = ZERO_STREAK
        child.userprofile.save(update_fields=["streak"])

        result = build_parent_progress_summary(parent, child)

        self.assertTrue(result.success)
        codes = {item["code"] for item in result.data["concerns"]}
        self.assertIn(CONCERN_LOW_COMPLETION, codes)
        self.assertIn(CONCERN_LOW_SCORE, codes)
        self.assertIn(CONCERN_NO_STREAK, codes)
