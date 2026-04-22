from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from inregistrare.models import Profile

from .models import (
    CodeExercise,
    CoopSession,
    DailyChallenge,
    FeatureFlag,
    LearningPath,
    LearningPathLesson,
    Lesson,
    LessonProgress,
    LessonStreak,
    Subject,
    Test,
)
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
        # New step-based template: has HUD, steps, and quiz
        self.assertContains(response, "lesson-hud")
        self.assertContains(response, "lesson-step")
        self.assertContains(response, "data-ls-quiz")
        self.assertContains(response, "La ce foloseste o variabila?")
        self.assertContains(response, "Verifica raspunsul")

    def test_python_track_for_older_students_renders_code_snippets(self):
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
        # New step-based template with code examples for older students
        self.assertContains(response, "lesson-step")
        self.assertContains(response, "Python Mission")
        self.assertContains(response, "Cod complet")
        self.assertContains(response, "ls-code")

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
        # New step-based template: junior track uses mentor bubble with junior text
        self.assertContains(response, "lesson-step")
        self.assertContains(response, "Junior Mission")
        self.assertContains(response, "Citeste cu atentie")

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

        with patch(
            "estudy.views._resolve_subject_entry_slug", return_value=lesson.slug
        ):
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
        start_date = timezone.localdate() - timezone.timedelta(days=1000)
        junior_lesson = Lesson.objects.create(
            subject=python_subject,
            title="Junior Entry",
            content="Content",
            date=start_date,
            age_bracket=Lesson.AGE_8_10,
        )
        Lesson.objects.create(
            subject=python_subject,
            title="Code Entry",
            content="Content",
            date=start_date + timezone.timedelta(days=1),
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
        start_date = timezone.localdate() - timezone.timedelta(days=1000)
        Lesson.objects.create(
            subject=python_subject,
            title="Junior Entry",
            content="Content",
            date=start_date,
            age_bracket=Lesson.AGE_8_10,
        )
        older_lesson = Lesson.objects.create(
            subject=python_subject,
            title="Code Entry",
            content="Content",
            date=start_date + timezone.timedelta(days=1),
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

    def test_lessons_list_defaults_to_junior_python_entry_when_age_missing(self):
        python_subject = Subject.objects.create(name="Coding Quest")
        start_date = timezone.localdate() - timezone.timedelta(days=1000)
        junior_lesson = Lesson.objects.create(
            subject=python_subject,
            title="Junior Entry",
            content="Content",
            date=start_date,
            age_bracket=Lesson.AGE_8_10,
        )
        Lesson.objects.create(
            subject=python_subject,
            title="Code Entry",
            content="Content",
            date=start_date + timezone.timedelta(days=1),
            age_bracket=Lesson.AGE_11_13,
        )

        response = self.client.get(reverse("estudy:lessons_list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["python_entry_slug"], junior_lesson.slug)
        self.assertContains(
            response,
            reverse("estudy:lesson_detail", kwargs={"slug": junior_lesson.slug}),
        )
        self.assertContains(response, "Junior implicit pana alegi varsta")

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


class StreakServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="streaker", email="s@example.com", password="pass1234"
        )
        self.subject = Subject.objects.create(name="Streak Subject")

    def _create_lesson(self, title, days_offset=0):
        date = timezone.localdate() + timedelta(days=days_offset)
        return Lesson.objects.create(
            subject=self.subject, title=title, content="c", date=date
        )

    def test_streak_increases_on_consecutive_days(self):
        from .services.streaks import update_streak_on_completion

        today = timezone.now()
        l1 = self._create_lesson("Day1")
        l2 = self._create_lesson("Day2")
        LessonProgress.objects.create(
            user=self.user,
            lesson=l1,
            completed=True,
            completed_at=today - timedelta(days=1),
        )
        LessonProgress.objects.create(
            user=self.user, lesson=l2, completed=True, completed_at=today
        )
        result = update_streak_on_completion(self.user)
        self.assertTrue(result.success)
        self.assertEqual(result.data["current_streak"], 2)

    def test_streak_resets_when_gap(self):
        from .services.streaks import update_streak_on_completion

        today = timezone.now()
        l1 = self._create_lesson("Old")
        l2 = self._create_lesson("Today")
        LessonProgress.objects.create(
            user=self.user,
            lesson=l1,
            completed=True,
            completed_at=today - timedelta(days=3),
        )
        LessonProgress.objects.create(
            user=self.user, lesson=l2, completed=True, completed_at=today
        )
        result = update_streak_on_completion(self.user)
        self.assertEqual(result.data["current_streak"], 1)

    def test_longest_streak_preserved(self):
        from .services.streaks import update_streak_on_completion

        profile = self.user.userprofile
        profile.longest_streak = 10
        profile.save(update_fields=["longest_streak"])
        today = timezone.now()
        l1 = self._create_lesson("Today")
        LessonProgress.objects.create(
            user=self.user, lesson=l1, completed=True, completed_at=today
        )
        result = update_streak_on_completion(self.user)
        self.assertEqual(result.data["current_streak"], 1)
        self.assertEqual(result.data["longest_streak"], 10)


class WorldMapServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="explorer", email="e@example.com", password="pass1234"
        )
        self.subject = Subject.objects.create(name="Map Subject")

    def _create_lesson(self, title, days_offset=0):
        date = timezone.localdate() + timedelta(days=days_offset)
        return Lesson.objects.create(
            subject=self.subject, title=title, content="c", date=date
        )

    def test_build_world_map_states(self):
        from .services.world_map import build_world_map

        path = LearningPath.objects.create(
            title="Test Path", slug="test-path", description="d"
        )
        l1 = self._create_lesson("L1", -2)
        l2 = self._create_lesson("L2", -1)
        l3 = self._create_lesson("L3", 0)
        LearningPathLesson.objects.create(path=path, lesson=l1, order=1)
        LearningPathLesson.objects.create(path=path, lesson=l2, order=2)
        LearningPathLesson.objects.create(path=path, lesson=l3, order=3)
        LessonProgress.objects.create(user=self.user, lesson=l1, completed=True)

        result = build_world_map(self.user)
        self.assertTrue(result.success)
        nodes = result.data["paths"][0]["nodes"]
        self.assertEqual(nodes[0]["state"], "completed")
        self.assertEqual(nodes[1]["state"], "available")
        self.assertEqual(nodes[2]["state"], "locked")

    def test_empty_paths(self):
        from .services.world_map import build_world_map

        result = build_world_map(self.user)
        self.assertTrue(result.success)
        self.assertEqual(result.data["paths"], [])


class ShareCardServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="winner", email="w@example.com", password="pass1234"
        )
        self.subject = Subject.objects.create(name="Share Subject")

    def _create_lesson(self, title, days_offset=0):
        date = timezone.localdate() + timedelta(days=days_offset)
        return Lesson.objects.create(
            subject=self.subject, title=title, content="c", date=date
        )

    def test_share_card_returns_data_for_completed_lesson(self):
        from .services.share_card import build_share_card_context

        lesson = self._create_lesson("Done Lesson")
        LessonProgress.objects.create(
            user=self.user,
            lesson=lesson,
            completed=True,
            completed_at=timezone.now(),
            points_earned=50,
        )
        result = build_share_card_context(self.user, lesson)
        self.assertTrue(result.success)
        self.assertEqual(result.data["lesson_title"], "Done Lesson")
        self.assertEqual(result.data["xp_earned"], 50)

    def test_share_card_fails_for_incomplete_lesson(self):
        from .services.share_card import build_share_card_context

        lesson = self._create_lesson("Not Done")
        result = build_share_card_context(self.user, lesson)
        self.assertFalse(result.success)

    def test_share_card_view_returns_200(self):
        self.client.login(username="winner", password="pass1234")
        lesson = self._create_lesson("View Lesson")
        LessonProgress.objects.create(
            user=self.user,
            lesson=lesson,
            completed=True,
            completed_at=timezone.now(),
            points_earned=30,
        )
        url = reverse("estudy:share_card", kwargs={"slug": lesson.slug})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "View Lesson")
        self.assertContains(resp, "UNITEX")

    def test_share_card_view_returns_404_for_incomplete(self):
        self.client.login(username="winner", password="pass1234")
        lesson = self._create_lesson("Incomplete")
        url = reverse("estudy:share_card", kwargs={"slug": lesson.slug})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)


# ── Daily Challenge service tests ──────────────────────────────────────


class DailyChallengeServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="challenger", email="c@example.com", password="pass1234"
        )
        self.subject = Subject.objects.create(name="Challenge Subject")

    def _create_lesson(self, title, days_offset=0):
        date = timezone.localdate() + timedelta(days=days_offset)
        return Lesson.objects.create(
            subject=self.subject, title=title, content="c", date=date
        )

    def test_get_todays_challenge_returns_active_challenge(self):
        from .services.daily_challenge import get_todays_challenge

        lesson = self._create_lesson("Daily L")
        today = timezone.localdate()
        DailyChallenge.objects.create(
            title="Today's challenge",
            description="Do it",
            lesson=lesson,
            start_date=today,
            end_date=today,
            xp_bonus=75,
        )
        result = get_todays_challenge(self.user)
        self.assertTrue(result.success)
        self.assertEqual(result.data["challenge"].title, "Today's challenge")
        self.assertFalse(result.data["completed"])

    def test_get_todays_challenge_shows_completed(self):
        from .services.daily_challenge import get_todays_challenge

        lesson = self._create_lesson("Daily L2")
        today = timezone.localdate()
        DailyChallenge.objects.create(
            title="Done challenge",
            description="Done",
            lesson=lesson,
            start_date=today,
            end_date=today,
        )
        LessonProgress.objects.create(
            user=self.user,
            lesson=lesson,
            completed=True,
            completed_at=timezone.now(),
        )
        result = get_todays_challenge(self.user)
        self.assertTrue(result.success)
        self.assertTrue(result.data["completed"])

    def test_get_todays_challenge_none_active(self):
        from .services.daily_challenge import get_todays_challenge

        result = get_todays_challenge(self.user)
        self.assertFalse(result.success)

    def test_get_challenge_time_remaining_positive(self):
        from .services.daily_challenge import get_challenge_time_remaining

        seconds = get_challenge_time_remaining()
        self.assertGreaterEqual(seconds, 0)
        self.assertLessEqual(seconds, 86400)

    def test_has_user_completed_challenge_false_no_lesson(self):
        from .services.daily_challenge import has_user_completed_challenge

        challenge = DailyChallenge.objects.create(
            title="No lesson",
            description="x",
            start_date=timezone.localdate(),
            end_date=timezone.localdate(),
        )
        self.assertFalse(has_user_completed_challenge(self.user, challenge))

    def test_has_user_completed_challenge_true(self):
        from .services.daily_challenge import has_user_completed_challenge

        lesson = self._create_lesson("CL")
        challenge = DailyChallenge.objects.create(
            title="With lesson",
            description="x",
            lesson=lesson,
            start_date=timezone.localdate(),
            end_date=timezone.localdate(),
        )
        LessonProgress.objects.create(
            user=self.user,
            lesson=lesson,
            completed=True,
            completed_at=timezone.now(),
        )
        self.assertTrue(has_user_completed_challenge(self.user, challenge))


# ── Coop session service tests ─────────────────────────────────────────


class CoopServiceTests(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(
            username="host", email="h@example.com", password="pass1234"
        )
        self.guest = User.objects.create_user(
            username="guest", email="g@example.com", password="pass1234"
        )
        self.subject = Subject.objects.create(name="Coop Subject")
        self.lesson = Lesson.objects.create(
            subject=self.subject,
            title="Coop Lesson",
            content="c",
            date=timezone.localdate(),
        )
        # enable feature flag
        FeatureFlag.objects.create(key="coop_mode_enabled", enabled=True)

    def test_create_coop_session(self):
        from .services.coop import create_coop_session

        result = create_coop_session(self.host, self.lesson)
        self.assertTrue(result.success)
        self.assertEqual(len(result.data["session_code"]), 6)
        self.assertEqual(result.data["status"], "waiting")

    def test_create_coop_session_disabled(self):
        from .services.coop import create_coop_session

        FeatureFlag.objects.filter(key="coop_mode_enabled").update(enabled=False)
        result = create_coop_session(self.host, self.lesson)
        self.assertFalse(result.success)

    def test_join_coop_session(self):
        from .services.coop import create_coop_session, join_coop_session

        create_result = create_coop_session(self.host, self.lesson)
        code = create_result.data["session_code"]
        join_result = join_coop_session(self.guest, code)
        self.assertTrue(join_result.success)
        self.assertEqual(join_result.data["status"], "active")
        self.assertEqual(join_result.data["host_username"], "host")

    def test_join_own_session_fails(self):
        from .services.coop import create_coop_session, join_coop_session

        create_result = create_coop_session(self.host, self.lesson)
        code = create_result.data["session_code"]
        join_result = join_coop_session(self.host, code)
        self.assertFalse(join_result.success)

    def test_join_invalid_code_fails(self):
        from .services.coop import join_coop_session

        result = join_coop_session(self.guest, "ZZZZZZ")
        self.assertFalse(result.success)

    def test_complete_coop_session(self):
        from .services.coop import (
            complete_coop_session,
            create_coop_session,
            join_coop_session,
        )

        create_result = create_coop_session(self.host, self.lesson)
        code = create_result.data["session_code"]
        join_coop_session(self.guest, code)
        session = CoopSession.objects.get(session_code=code)
        result = complete_coop_session(session)
        self.assertTrue(result.success)
        # both users should have progress
        self.assertTrue(
            LessonProgress.objects.filter(
                user=self.host, lesson=self.lesson, completed=True
            ).exists()
        )
        self.assertTrue(
            LessonProgress.objects.filter(
                user=self.guest, lesson=self.lesson, completed=True
            ).exists()
        )

    def test_complete_without_guest_fails(self):
        from .services.coop import complete_coop_session, create_coop_session

        create_result = create_coop_session(self.host, self.lesson)
        session = CoopSession.objects.get(
            session_code=create_result.data["session_code"]
        )
        result = complete_coop_session(session)
        self.assertFalse(result.success)

    def test_coop_create_view_returns_json(self):
        self.client.login(username="host", password="pass1234")
        url = reverse("estudy:coop_create")
        resp = self.client.post(url, {"lesson_slug": self.lesson.slug})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("session_code", data)

    def test_coop_join_view_returns_json(self):
        self.client.login(username="host", password="pass1234")
        create_resp = self.client.post(
            reverse("estudy:coop_create"), {"lesson_slug": self.lesson.slug}
        )
        code = create_resp.json()["session_code"]
        self.client.login(username="guest", password="pass1234")
        resp = self.client.post(reverse("estudy:coop_join"), {"session_code": code})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "active")


# ── Streak leaderboard service tests ────────────────────────────────────


class StreakLeaderboardServiceTests(TestCase):
    def setUp(self):
        self.subject = Subject.objects.create(
            name="Streak LB Subject", slug="streak-lb-subject"
        )
        self.user1 = User.objects.create_user(
            username="streaker1", email="s1@example.com", password="pass1234"
        )
        self.user2 = User.objects.create_user(
            username="streaker2", email="s2@example.com", password="pass1234"
        )
        FeatureFlag.objects.create(key="streak_leaderboard_enabled", enabled=True)

    def test_get_streak_leaderboard_ordered(self):
        from .services.skill_leaderboard import get_streak_leaderboard

        LessonStreak.objects.create(
            user=self.user1,
            subject=self.subject,
            current_streak=5,
            longest_streak=10,
        )
        LessonStreak.objects.create(
            user=self.user2,
            subject=self.subject,
            current_streak=8,
            longest_streak=8,
        )
        result = get_streak_leaderboard(self.subject)
        self.assertTrue(result.success)
        entries = result.data["entries"]
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["username"], "streaker2")
        self.assertEqual(entries[0]["current_streak"], 8)
        self.assertEqual(entries[1]["username"], "streaker1")

    def test_get_streak_leaderboard_empty(self):
        from .services.skill_leaderboard import get_streak_leaderboard

        result = get_streak_leaderboard(self.subject)
        self.assertTrue(result.success)
        self.assertEqual(result.data["entries"], [])

    def test_get_streak_leaderboard_disabled(self):
        from .services.skill_leaderboard import get_streak_leaderboard

        FeatureFlag.objects.filter(key="streak_leaderboard_enabled").update(
            enabled=False
        )
        result = get_streak_leaderboard(self.subject)
        self.assertFalse(result.success)

    def test_streak_leaderboard_avatar_initial(self):
        from .services.skill_leaderboard import get_streak_leaderboard

        LessonStreak.objects.create(
            user=self.user1,
            subject=self.subject,
            current_streak=3,
            longest_streak=3,
        )
        result = get_streak_leaderboard(self.subject)
        self.assertEqual(result.data["entries"][0]["avatar_initial"], "S")

    def test_streak_leaderboard_view_returns_json(self):
        self.client.login(username="streaker1", password="pass1234")
        LessonStreak.objects.create(
            user=self.user1,
            subject=self.subject,
            current_streak=4,
            longest_streak=4,
        )
        url = reverse(
            "estudy:streak_leaderboard", kwargs={"subject_slug": self.subject.slug}
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["current_streak"], 4)

    def test_streak_leaderboard_view_returns_403_when_disabled(self):
        self.client.login(username="streaker1", password="pass1234")
        FeatureFlag.objects.filter(key="streak_leaderboard_enabled").update(
            enabled=False
        )
        url = reverse(
            "estudy:streak_leaderboard", kwargs={"subject_slug": self.subject.slug}
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 403)
