from datetime import timedelta
from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from inregistrare.forms import InregistrareFormular, LoginFormular, ProfileForm

from .models import (
    Classroom,
    ClassroomMembership,
    LearnerCheckIn,
    Lesson,
    LessonProgress,
    Notification,
    ParentChildLink,
    Subject,
    UserProfile,
)
from .services.notifications_enhanced import NotificationTemplate, send_streak_reminder
from .services.today_learning import record_learner_checkin

USER_PASSWORD = "pass1234"
MOJIBAKE_PATTERNS = (
    "Р",
    "рџ",
    "вЂ",
    "вњ",
    "в¬",
    "вЏ",
    "Г®",
    "В·",
    "И™",
    "И›",
    "Дѓ",
)


class DashboardHardeningSmokeTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="hardening_student", password=USER_PASSWORD
        )
        self.teacher = User.objects.create_user(
            username="hardening_teacher", password=USER_PASSWORD
        )
        self.teacher.userprofile.status = UserProfile.ROLE_PROFESSOR
        self.teacher.userprofile.save(update_fields=["status"])
        self.parent = User.objects.create_user(
            username="hardening_parent", password=USER_PASSWORD
        )
        self.parent.userprofile.status = UserProfile.ROLE_PARENT
        self.parent.userprofile.save(update_fields=["status"])

        self.subject = Subject.objects.create(name="Hardening")
        self.lesson = Lesson.objects.create(
            subject=self.subject,
            title="Hardening Lesson",
            content="content",
            date=timezone.localdate(),
        )
        self.classroom = Classroom.objects.create(
            name="Hardening Class", owner=self.teacher
        )
        ClassroomMembership.objects.create(
            classroom=self.classroom,
            user=self.student,
            role=ClassroomMembership.ROLE_STUDENT,
            approved=True,
        )
        ParentChildLink.objects.create(
            parent=self.parent,
            child=self.student,
            approved=True,
        )
        record_learner_checkin(
            self.student,
            self.lesson,
            mood=LearnerCheckIn.MOOD_NEEDS_HELP,
            difficulty=LearnerCheckIn.DIFFICULTY_TOO_HARD,
        )

    def test_student_dashboard_contains_today_plan_payload_and_block(self):
        self.client.login(username="hardening_student", password=USER_PASSWORD)

        response = self.client.get(reverse("estudy:student_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("today_plan", response.context)
        self.assertIn("practice_plan", response.context)
        self.assertIn("age_track", response.context)
        self.assertContains(response, "Planul de azi")
        self.assertContains(response, "Recapitulare")

    def test_lesson_detail_contains_checkin_controls(self):
        self.client.login(username="hardening_student", password=USER_PASSWORD)

        response = self.client.get(
            reverse("estudy:lesson_detail", kwargs={"slug": self.lesson.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Check-in rapid")
        self.assertContains(response, "Am inteles")
        self.assertContains(response, "Am nevoie de ajutor")
        self.assertContains(response, "Prea usor")
        self.assertContains(response, "Prea greu")

    def test_teacher_dashboard_contains_support_payload_and_block(self):
        self.client.login(username="hardening_teacher", password=USER_PASSWORD)

        response = self.client.get(reverse("estudy:teacher_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("students_needing_help", response.context)
        self.assertIn("weak_topics", response.context)
        self.assertIn("checkins", response.context)
        self.assertContains(response, "Elevi care au nevoie de ajutor")
        self.assertContains(response, "A cerut ajutor")

    def test_parent_dashboard_contains_weekly_summary_block(self):
        self.client.login(username="hardening_parent", password=USER_PASSWORD)

        response = self.client.get(reverse("estudy:parent_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("children", response.context)
        self.assertIn("weekly_summaries", response.context)
        self.assertContains(response, "Saptamana aceasta")
        self.assertContains(response, "discutie scurta")


class NotificationTextHardeningTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="hardening_notify", password=USER_PASSWORD
        )
        self.subject = Subject.objects.create(name="Reminder Subject")
        for lesson in Lesson.objects.all():
            LessonProgress.objects.update_or_create(
                user=self.user,
                lesson=lesson,
                defaults={"completed": True, "completed_at": timezone.now()},
            )
        self.completed_lesson = Lesson.objects.create(
            subject=self.subject,
            title="Completed Reminder Lesson",
            content="content",
            date=timezone.localdate(),
        )
        self.open_lesson_one = Lesson.objects.create(
            subject=self.subject,
            title="Open Reminder Lesson One",
            content="content",
            date=timezone.localdate(),
        )
        self.open_lesson_two = Lesson.objects.create(
            subject=self.subject,
            title="Open Reminder Lesson Two",
            content="content",
            date=timezone.localdate(),
        )
        LessonProgress.objects.create(
            user=self.user,
            lesson=self.completed_lesson,
            completed=True,
            completed_at=timezone.now(),
        )

    def test_notification_templates_do_not_contain_mojibake(self):
        visible_text = []
        for template in NotificationTemplate.TEMPLATES.values():
            visible_text.append(template["title"])
            visible_text.append(template["message"])

        joined = "\n".join(visible_text)

        for pattern in MOJIBAKE_PATTERNS:
            self.assertNotIn(pattern, joined)
        self.assertIn("E timpul sa inveti!", joined)
        self.assertIn("Raport despre progresul copilului", joined)

    def test_streak_reminder_uses_real_incomplete_lesson_count(self):
        profile = self.user.userprofile
        profile.streak = 3
        profile.last_activity_at = timezone.now() - timedelta(hours=21)
        profile.save(update_fields=["streak", "last_activity_at"])

        notification = send_streak_reminder(self.user)

        self.assertIsNotNone(notification)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(notification.title, "E timpul sa inveti!")
        self.assertIn("Ai 2 lectii nefinalizate", notification.message)
        self.assertNotIn("Ai 5 lectii nefinalizate", notification.message)


class AccountFormTextHardeningTests(TestCase):
    def test_account_forms_use_clean_romanian_ascii_labels(self):
        signup_form = InregistrareFormular()
        login_form = LoginFormular()
        profile_form = ProfileForm()

        visible_text = [
            signup_form.fields["email"].label,
            signup_form.fields["age"].label,
            signup_form.fields["accept_terms"].label,
            signup_form.fields["password1"].label,
            signup_form.fields["password2"].label,
            signup_form.fields["role"].help_text,
            signup_form.fields["accept_terms"].help_text,
            login_form.fields["password"].label,
            profile_form.fields["email"].label,
            profile_form.fields["age"].label,
            profile_form.fields["bio"].widget.attrs["placeholder"],
        ]
        joined = "\n".join(visible_text)

        for pattern in MOJIBAKE_PATTERNS:
            self.assertNotIn(pattern, joined)
        self.assertIn("Adresa de email", joined)
        self.assertIn("Varsta", joined)
        self.assertIn("Accept Termenii si conditiile", joined)


class LessonUiRegressionTests(TestCase):
    def test_dark_reflection_buttons_define_readable_text_color(self):
        css = (
            Path(__file__).resolve().parent / "static" / "estudy" / "lesson.css"
        ).read_text(encoding="utf-8")

        self.assertIn(".ls-reflection-scale__btn", css)
        self.assertIn("color: var(--lk-text);", css)
        self.assertIn('html[data-theme="dark"] .ls-reflection-scale__btn', css)
        self.assertIn("color: #F8FAFC;", css)

    def test_achievement_toasts_are_saved_and_not_stacked(self):
        js = (
            Path(__file__).resolve().parent / "static" / "estudy" / "lesson.js"
        ).read_text(encoding="utf-8")
        template = (
            Path(__file__).resolve().parent
            / "templates"
            / "estudy"
            / "lesson_detail.html"
        ).read_text(encoding="utf-8")

        self.assertIn("data-lesson-completed", template)
        self.assertIn("initialLessonCompleted", js)
        self.assertIn("earnedAchievements: [...earnedAchievements]", js)
        self.assertIn("achievementToastShownThisPage", js)
        self.assertNotIn(
            "document.querySelectorAll('.ls-achievement-toast').length", js
        )
