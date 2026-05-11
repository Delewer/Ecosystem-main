from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from inregistrare.models import Profile

from .models import (
    Classroom,
    ClassroomMembership,
    LearnerCheckIn,
    Lesson,
    LessonProgress,
    ParentChildLink,
    Subject,
    Test,
    TestAttempt,
    UserProfile,
)
from .services.today_learning import (
    AGE_TRACK_JUNIOR,
    AGE_TRACK_OLDER,
    build_parent_weekly_summary,
    build_teacher_support_snapshot,
    build_today_learning_plan,
    record_learner_checkin,
)

USER_PASSWORD = "pass1234"


class TodayLearningPlanTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="learner", password=USER_PASSWORD)
        for lesson in Lesson.objects.all():
            LessonProgress.objects.get_or_create(
                user=self.user,
                lesson=lesson,
                defaults={"completed": True, "completed_at": timezone.now()},
            )
        self.subject = Subject.objects.create(name="Coding Quest")
        self.start_date = timezone.localdate() - timezone.timedelta(days=5)

    def _set_age(self, age: int):
        Profile.objects.update_or_create(
            user=self.user,
            defaults={"email": "learner@example.com", "age": age},
        )

    def _lesson(self, title: str, age_bracket: str, offset: int = 0) -> Lesson:
        return Lesson.objects.create(
            subject=self.subject,
            title=title,
            content="content",
            date=self.start_date + timezone.timedelta(days=offset),
            age_bracket=age_bracket,
        )

    def test_today_plan_uses_junior_track_for_younger_children(self):
        junior = self._lesson("Junior Path", Lesson.AGE_8_10)
        self._lesson("Older Path", Lesson.AGE_11_13)
        self._set_age(9)

        plan = build_today_learning_plan(self.user)

        self.assertEqual(plan["age_track"]["key"], AGE_TRACK_JUNIOR)
        self.assertEqual(plan["next_lesson"]["lesson"].id, junior.id)

    def test_today_plan_uses_older_track_for_older_children(self):
        self._lesson("Junior Path", Lesson.AGE_8_10)
        older = self._lesson("Older Path", Lesson.AGE_11_13)
        self._set_age(14)

        plan = build_today_learning_plan(self.user)

        self.assertEqual(plan["age_track"]["key"], AGE_TRACK_OLDER)
        self.assertEqual(plan["next_lesson"]["lesson"].id, older.id)

    def test_recent_mistake_and_checkin_drive_review_task(self):
        lesson = self._lesson("Hard Topic", Lesson.AGE_11_13)
        quiz = Test.objects.create(
            lesson=lesson,
            question="Pick A",
            correct_answer="A",
            wrong_answers=["B", "C"],
        )
        TestAttempt.objects.create(
            test=quiz,
            user=self.user,
            selected_answer="B",
            is_correct=False,
        )
        record_learner_checkin(
            self.user,
            lesson,
            mood=LearnerCheckIn.MOOD_NEEDS_HELP,
            difficulty=LearnerCheckIn.DIFFICULTY_TOO_HARD,
        )

        plan = build_today_learning_plan(self.user)

        self.assertEqual(plan["review_task"]["lesson"].id, lesson.id)
        self.assertEqual(plan["recent_mistakes"][0]["lesson"].id, lesson.id)

    def test_checkin_post_updates_existing_record(self):
        lesson = self._lesson("Check-in Lesson", Lesson.AGE_11_13)
        self.client.login(username="learner", password=USER_PASSWORD)

        response = self.client.post(
            reverse("estudy:submit_learner_checkin", kwargs={"slug": lesson.slug}),
            {
                "mood": LearnerCheckIn.MOOD_NEEDS_HELP,
                "difficulty": LearnerCheckIn.DIFFICULTY_TOO_HARD,
                "note": "Need the first step again.",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(LearnerCheckIn.objects.count(), 1)
        checkin = LearnerCheckIn.objects.get()
        self.assertTrue(checkin.help_requested)

        self.client.post(
            reverse("estudy:submit_learner_checkin", kwargs={"slug": lesson.slug}),
            {
                "mood": LearnerCheckIn.MOOD_UNDERSTOOD,
                "difficulty": LearnerCheckIn.DIFFICULTY_JUST_RIGHT,
            },
        )

        self.assertEqual(LearnerCheckIn.objects.count(), 1)
        checkin.refresh_from_db()
        self.assertFalse(checkin.help_requested)

    def test_student_dashboard_smoke_renders_today_plan(self):
        self._lesson("Dashboard Lesson", Lesson.AGE_11_13)
        self.client.login(username="learner", password=USER_PASSWORD)

        response = self.client.get(reverse("estudy:student_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Planul de azi")


class AdultSupportDashboardTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username="teacher_support", password=USER_PASSWORD
        )
        self.teacher.userprofile.status = UserProfile.ROLE_PROFESSOR
        self.teacher.userprofile.save(update_fields=["status"])
        self.parent = User.objects.create_user(
            username="parent_support", password=USER_PASSWORD
        )
        self.parent.userprofile.status = UserProfile.ROLE_PARENT
        self.parent.userprofile.save(update_fields=["status"])
        self.child = User.objects.create_user(
            username="child_support", password=USER_PASSWORD
        )
        self.subject = Subject.objects.create(name="Support Subject")
        self.lesson = Lesson.objects.create(
            subject=self.subject,
            title="Support Lesson",
            content="content",
            date=timezone.localdate(),
        )
        self.quiz = Test.objects.create(
            lesson=self.lesson,
            question="Pick A",
            correct_answer="A",
            wrong_answers=["B", "C"],
        )
        self.classroom = Classroom.objects.create(
            name="Support Class", owner=self.teacher
        )
        ClassroomMembership.objects.create(
            classroom=self.classroom,
            user=self.child,
            role=ClassroomMembership.ROLE_STUDENT,
            approved=True,
        )
        ParentChildLink.objects.create(
            parent=self.parent,
            child=self.child,
            approved=True,
        )

    def test_teacher_support_snapshot_includes_help_checkin_and_weak_topic(self):
        TestAttempt.objects.create(
            test=self.quiz,
            user=self.child,
            selected_answer="B",
            is_correct=False,
        )
        record_learner_checkin(
            self.child,
            self.lesson,
            mood=LearnerCheckIn.MOOD_NEEDS_HELP,
            difficulty=LearnerCheckIn.DIFFICULTY_TOO_HARD,
        )

        snapshot = build_teacher_support_snapshot(self.teacher)

        self.assertEqual(
            snapshot["students_needing_help"][0]["student"].id, self.child.id
        )
        self.assertEqual(
            snapshot["weak_topics"][0]["test__lesson__title"], self.lesson.title
        )

    def test_parent_weekly_summary_uses_progress_mistakes_and_checkins(self):
        progress = LessonProgress.objects.create(
            user=self.child,
            lesson=self.lesson,
            completed=True,
            completed_at=timezone.now(),
        )
        progress.save()
        TestAttempt.objects.create(
            test=self.quiz,
            user=self.child,
            selected_answer="B",
            is_correct=False,
        )
        record_learner_checkin(
            self.child,
            self.lesson,
            mood=LearnerCheckIn.MOOD_NEEDS_HELP,
            difficulty=LearnerCheckIn.DIFFICULTY_TOO_HARD,
        )

        summary = build_parent_weekly_summary([self.child])[0]

        self.assertEqual(summary["completed_count"], 1)
        self.assertEqual(summary["mistake_count"], 1)
        self.assertTrue(summary["help_checkins"])
        self.assertIn(self.lesson.title, summary["discussion_prompt"])

    def test_teacher_and_parent_dashboards_smoke_render_support_blocks(self):
        record_learner_checkin(
            self.child,
            self.lesson,
            mood=LearnerCheckIn.MOOD_NEEDS_HELP,
            difficulty=LearnerCheckIn.DIFFICULTY_TOO_HARD,
        )

        self.client.login(username="teacher_support", password=USER_PASSWORD)
        teacher_response = self.client.get(reverse("estudy:teacher_dashboard"))
        self.assertEqual(teacher_response.status_code, 200)
        self.assertContains(teacher_response, "Elevi care au nevoie de ajutor")

        self.client.logout()
        self.client.login(username="parent_support", password=USER_PASSWORD)
        parent_response = self.client.get(reverse("estudy:parent_dashboard"))
        self.assertEqual(parent_response.status_code, 200)
        self.assertContains(parent_response, "Saptamana aceasta")
