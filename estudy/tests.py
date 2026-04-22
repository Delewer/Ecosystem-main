from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from inregistrare.models import Profile

from .models import CodeExercise, Lesson, LessonProgress, Subject, Test
from .views import PYTHON_TRACK_SUBJECT_NAMES, _resolve_subject_entry_slug


class LessonViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="tester", email="t@example.com", password="pass1234"
        )
        self.client.login(username="tester", password="pass1234")
        self.subject = Subject.objects.create(name="Test Subject")

    def _create_lesson(self, title, days_offset=0):
        date = timezone.localdate() + timezone.timedelta(days=days_offset)
        lesson = Lesson.objects.create(
            subject=self.subject,
            title=title,
            content="Content",
            date=date,
        )
        return lesson

    def test_lesson_detail_redirects_if_previous_not_completed(self):
        # create two lessons in sequence: older (required) and newer
        l1 = self._create_lesson("First", days_offset=-2)
        l2 = self._create_lesson("Second", days_offset=0)

        url = reverse("estudy:lesson_detail", kwargs={"slug": l2.slug})
        resp = self.client.get(url)
        # should redirect to the blocking lesson (first)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(l1.slug, resp.url)

    def test_toggle_lesson_completion_marks_completed(self):
        lesson = self._create_lesson("Solo", days_offset=0)
        url = reverse("estudy:toggle_lesson_completion", kwargs={"slug": lesson.slug})
        resp = self.client.post(url, {"seconds": "45"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("completed"))
        self.assertIn("progress_percent", data)
        # verify LessonProgress exists and is completed
        progress = LessonProgress.objects.filter(user=self.user, lesson=lesson).first()
        self.assertIsNotNone(progress)
        self.assertTrue(progress.completed)

    def test_lesson_detail_theory_track_hides_robot_lab_and_keeps_quiz_copy(self):
        lesson = self._create_lesson("Solo", days_offset=0)
        Test.objects.create(
            lesson=lesson,
            question="La ce foloseste o variabila?",
            correct_answer="Pastreaza o valoare",
            wrong_answers=["Trimite email", "Sterge programul", "Deseneaza un cerc"],
            explanation="Variabila pastreaza o valoare pe care o poti refolosi.",
        )
        response = self.client.get(
            reverse("estudy:lesson_detail", kwargs={"slug": lesson.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Exemple ghidate si intrebari")
        self.assertNotContains(response, "Misiune Robot Lab")
        self.assertNotContains(response, "Previzualizare live")
        self.assertContains(response, "Practica")
        self.assertContains(response, "Trimite raspunsul")
        self.assertContains(response, "Deschide / inchide testul")
        self.assertNotContains(
            response,
            '\\nvarsta = 12\\nprint(f"Salut, {nume}! Ai {varsta} ani.")',
        )

    def test_python_track_for_older_students_renders_robot_lab_code_mode(self):
        python_subject = Subject.objects.create(name="Coding Quest")
        lesson = Lesson.objects.create(
            subject=python_subject,
            title="Python Mission",
            content="Content",
            date=timezone.localdate(),
            age_bracket=Lesson.AGE_11_13,
        )
        response = self.client.get(
            reverse("estudy:lesson_detail", kwargs={"slug": lesson.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Robot Lab cu Python")
        self.assertContains(response, "Misiune Robot Lab")
        self.assertContains(response, "Ghideaza-l pe Robo spre terminal.")
        self.assertContains(response, "Previzualizare live")

    def test_python_track_for_junior_students_uses_visual_mode(self):
        python_subject = Subject.objects.create(name="Coding Quest")
        lesson = Lesson.objects.create(
            subject=python_subject,
            title="Junior Mission",
            content="Content",
            date=timezone.localdate(),
            age_bracket=Lesson.AGE_8_10,
        )
        response = self.client.get(
            reverse("estudy:lesson_detail", kwargs={"slug": lesson.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Puzzle si potriviri")
        self.assertContains(response, "Incepe jocul vizual")
        self.assertContains(response, "Labirintul lui Robo")
        self.assertContains(response, "Culori si reguli")
        self.assertContains(response, "Carti secrete")
        self.assertNotContains(response, "Misiune Robot Lab")
        self.assertNotContains(response, "Previzualizare live")

    def test_lessons_list_hides_signup_cta_for_authenticated_user(self):
        self._create_lesson("List lesson", days_offset=0)
        response = self.client.get(reverse("estudy:lessons_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboardul meu")
        self.assertNotContains(response, 'href="/auth/signup/"')

    def test_lessons_list_promotes_python_module_when_python_lessons_exist(self):
        python_subject = Subject.objects.create(name="Coding Quest")
        lesson = Lesson.objects.create(
            subject=python_subject,
            title="Python Entry",
            content="Content",
            date=timezone.localdate(),
            age_bracket=Lesson.AGE_11_13,
        )

        with patch("estudy.views._resolve_subject_entry_slug", return_value=lesson.slug):
            response = self.client.get(reverse("estudy:lessons_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Programare")
        self.assertContains(response, "Intra in modul")
        self.assertContains(
            response,
            reverse("estudy:lesson_detail", kwargs={"slug": lesson.slug}),
        )

    def test_lessons_list_uses_junior_python_entry_for_younger_profile(self):
        python_subject = Subject.objects.create(name="Coding Quest")
        junior_lesson = Lesson.objects.create(
            subject=python_subject,
            title="Junior Entry",
            content="Content",
            date=timezone.localdate(),
            age_bracket=Lesson.AGE_8_10,
        )
        Lesson.objects.create(
            subject=python_subject,
            title="Code Entry",
            content="Content",
            date=timezone.localdate() + timezone.timedelta(days=1),
            age_bracket=Lesson.AGE_11_13,
        )
        Profile.objects.update_or_create(
            user=self.user,
            defaults={"email": self.user.email, "age": 9},
        )
        self.assertEqual(
            _resolve_subject_entry_slug(PYTHON_TRACK_SUBJECT_NAMES, self.user),
            junior_lesson.slug,
        )

        response = self.client.get(reverse("estudy:lessons_list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["python_entry_slug"], junior_lesson.slug)
        self.assertContains(
            response,
            reverse("estudy:lesson_detail", kwargs={"slug": junior_lesson.slug}),
        )
        self.assertContains(response, "Junior 8-10 ani")

    def test_lessons_list_uses_code_python_entry_for_older_profile(self):
        python_subject = Subject.objects.create(name="Coding Quest")
        Lesson.objects.create(
            subject=python_subject,
            title="Junior Entry",
            content="Content",
            date=timezone.localdate(),
            age_bracket=Lesson.AGE_8_10,
        )
        older_lesson = Lesson.objects.create(
            subject=python_subject,
            title="Code Entry",
            content="Content",
            date=timezone.localdate() + timezone.timedelta(days=1),
            age_bracket=Lesson.AGE_11_13,
        )
        Profile.objects.update_or_create(
            user=self.user,
            defaults={"email": self.user.email, "age": 12},
        )

        response = self.client.get(reverse("estudy:lessons_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse("estudy:lesson_detail", kwargs={"slug": older_lesson.slug}),
        )
        self.assertContains(response, "Code 11+ ani")

    def test_run_code_api_executes_and_returns_results(self):
        lesson = self._create_lesson("Exec", days_offset=0)
        exercise = CodeExercise.objects.create(
            lesson=lesson,
            title="Square",
            description="Return square of input",
            language="python",
            starter_code="import sys\nprint(int(sys.stdin.read())**2)",
            test_cases=[
                {"input": "2", "expected_output": "4", "description": "2^2"},
                {"input": "5", "expected_output": "25", "description": "5^2"},
            ],
        )
        api_url = reverse("estudy:run_code_api")
        resp = self.client.post(
            api_url,
            data={"exercise_id": exercise.id, "code": exercise.starter_code},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertIn("passed", payload)
        self.assertEqual(payload["passed"], 2)
        self.assertTrue(payload.get("is_correct"))
        # Ensure a submission object created
        from .models import CodeSubmission

        self.assertTrue(
            CodeSubmission.objects.filter(exercise=exercise, user=self.user).exists()
        )


class ModelsLogicTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="muser", email="m@example.com", password="pass1234"
        )
        # ensure profile created by signal
        self.profile = self.user.userprofile
        self.subject = Subject.objects.create(name="Logic Subject")

    def test_lessonprogress_mark_completed_awards_xp_and_points(self):
        lesson = Lesson.objects.create(
            subject=self.subject, title="L1", content="C", date=timezone.localdate()
        )
        progress = LessonProgress.objects.create(user=self.user, lesson=lesson)
        # initial xp
        initial_xp = self.profile.xp
        progress.mark_completed(seconds_spent=42)
        progress.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertTrue(progress.completed)
        self.assertIsNotNone(progress.completed_at)
        self.assertGreaterEqual(progress.points_earned, lesson.xp_reward)
        self.assertGreaterEqual(self.profile.xp, initial_xp + lesson.xp_reward)

    def test_userprofile_add_xp_levels_up_and_logs(self):
        initial_level = self.profile.level
        # give enough xp to level up multiple times
        self.profile.add_xp(300, reason="test XP")
        self.profile.refresh_from_db()
        # level should have increased at least once
        self.assertGreater(self.profile.level, initial_level)
        # ExperienceLog should be created
        from .models import ExperienceLog

        self.assertTrue(ExperienceLog.objects.filter(user=self.user).exists())

    def test_check_and_award_rewards_creates_badges_and_rewards(self):
        # create multiple lessons and mark them completed
        lessons = []
        for i in range(12):
            lesson = Lesson.objects.create(
                subject=self.subject,
                title=f"L{i}",
                content="C",
                date=timezone.localdate(),
            )
            lessons.append(lesson)
            LessonProgress.objects.create(
                user=self.user,
                lesson=lesson,
                completed=True,
                completed_at=timezone.now(),
            )

        # ensure no badges initially
        from .models import Reward, UserBadge, UserReward

        UserBadge.objects.filter(user=self.user).delete()
        UserReward.objects.filter(user=self.user).delete()

        # run the checker
        from .models import check_and_award_rewards

        check_and_award_rewards(self.user)
        # badges should be awarded
        self.assertTrue(UserBadge.objects.filter(user=self.user).exists())
        # reward for 10 lessons
        self.assertTrue(Reward.objects.filter(name__icontains="10 Lessons").exists())
        self.assertTrue(UserReward.objects.filter(user=self.user).exists())
        # profile streak and last_activity_at updated
        self.profile.refresh_from_db()
        self.assertIsNotNone(self.profile.last_activity_at)
        self.assertGreaterEqual(self.profile.streak, 1)
