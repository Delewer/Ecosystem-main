import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from inregistrare.models import Profile

from .models import RobotLabLevelProgress, RobotLabRun, UserProfile
from .services.robot_lab_runner_client import RobotLabRunnerUnavailableError

ROBOT_LAB_FLAGS_ON = {
    "robot_lab_enabled": {
        "enabled": True,
        "rollout_percentage": 100,
    }
}


@override_settings(ESTUDY_FEATURE_FLAGS=ROBOT_LAB_FLAGS_ON)
class RobotLabVerticalSliceApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="student_robot",
            email="student_robot@example.com",
            password="pass1234",
        )
        self.client.login(username="student_robot", password="pass1234")
        self.levels_url = reverse("estudy:robot_lab_levels_api")
        self.run_url = reverse("estudy:robot_lab_run_api")
        self.progress_url = reverse("estudy:robot_lab_progress_api")

    def test_levels_and_level_detail_endpoints(self):
        response = self.client.get(self.levels_url)
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("levels", payload)
        self.assertEqual(len(payload["levels"]), 6)
        self.assertEqual(payload["levels"][0]["id"], "W1-L01")
        self.assertTrue(payload["levels"][0]["unlocked"])
        self.assertFalse(payload["levels"][1]["unlocked"])

        detail_url = reverse("estudy:robot_lab_level_detail_api", args=["W1-L01"])
        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, 200)
        detail = detail_response.json()
        self.assertEqual(detail["id"], "W1-L01")
        self.assertIn("starter_code", detail)
        self.assertIn("grid", detail)
        self.assertEqual(detail["mode"], "junior")
        self.assertEqual(detail["ui_stage"], "buttons")

    def test_play_page_uses_romanian_ui_copy(self):
        response = self.client.get(reverse("estudy:robot_lab_play", args=["W1-L01"]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rucsacul misiunii")
        self.assertContains(response, "Ruleaza codul")
        self.assertContains(response, "Stare misiune")
        self.assertNotContains(response, "Mission backpack")
        self.assertNotContains(response, "Run code")

    def test_play_page_shows_profile_track_recommendation(self):
        Profile.objects.update_or_create(
            user=self.user,
            defaults={"email": self.user.email, "age": 12},
        )
        response = self.client.get(reverse("estudy:robot_lab_play", args=["W1-L01"]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recomandare dupa profil")
        self.assertContains(response, "Mod Cod")
        self.assertContains(response, "profil 12 ani")

    def test_locked_level_cannot_run(self):
        response = self.client.post(
            self.run_url,
            data=json.dumps({"level_id": "W1-L03", "student_code": "move()"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    @patch("estudy.services.robot_lab_runs.execute_robot_lab_code")
    def test_run_updates_progress_and_awards_xp_once(self, mock_execute):
        mock_execute.return_value = {
            "status": "ok",
            "error_type": "none",
            "primary_error": "",
            "execution_trace": [
                {"step": 1, "action": "move", "position": [1, 2], "dir": "E"},
                {"step": 2, "action": "move", "position": [1, 3], "dir": "E"},
            ],
            "final_state": {"position": [1, 3], "direction": "E"},
            "steps_used": 2,
            "duration_ms": 15,
        }

        payload = {"level_id": "W1-L01", "student_code": "move()\nmove()"}
        response_1 = self.client.post(
            self.run_url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response_1.status_code, 200)
        data_1 = response_1.json()
        self.assertTrue(data_1["solved"])
        self.assertEqual(data_1["xp_granted"], 20)
        self.assertIn("mentor", data_1)
        self.assertIn("progress", data_1)

        response_2 = self.client.post(
            self.run_url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response_2.status_code, 200)
        data_2 = response_2.json()
        self.assertEqual(data_2["xp_granted"], 0)

        progress = RobotLabLevelProgress.objects.get(user=self.user, level_id="W1-L01")
        self.assertTrue(progress.completed)
        self.assertEqual(progress.attempts_count, 2)
        self.assertEqual(progress.xp_awarded_total, 20)

        self.assertEqual(
            RobotLabRun.objects.filter(user=self.user, level_id="W1-L01").count(), 2
        )

        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.xp, 20)

        progress_response = self.client.get(self.progress_url)
        self.assertEqual(progress_response.status_code, 200)
        progress_payload = progress_response.json()
        self.assertEqual(progress_payload["completed_levels"], 1)
        # W1-L02 should unlock after W1-L01 completion.
        levels = {item["id"]: item for item in progress_payload["levels"]}
        self.assertTrue(levels["W1-L02"]["unlocked"])

    @override_settings(ROBOT_RUNNER_URL="", ROBOT_RUNNER_LOCAL_FALLBACK=True)
    def test_run_uses_local_runner_fallback_when_runner_url_missing(self):
        response = self.client.post(
            self.run_url,
            data=json.dumps(
                {
                    "level_id": "W1-L01",
                    "student_code": "right()\nright()\ndown()\nright()",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["solved"])
        self.assertEqual(payload["error_type"], "none")
        self.assertTrue(payload["execution_trace"])
        self.assertGreaterEqual(payload["duration_ms"], 0)
        self.assertIn("console_output", payload)
        self.assertIn("status_message", payload)

    @patch("estudy.services.robot_lab_runs.execute_robot_lab_code")
    def test_run_returns_controlled_error_when_runner_unavailable(self, mock_execute):
        mock_execute.side_effect = RobotLabRunnerUnavailableError("down")
        response = self.client.post(
            self.run_url,
            data=json.dumps({"level_id": "W1-L01", "student_code": "move()"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 503)
        payload = response.json()
        self.assertIn("error", payload)


@override_settings(ESTUDY_FEATURE_FLAGS=ROBOT_LAB_FLAGS_ON)
class RobotLabTeacherViewTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username="teacher_robot",
            email="teacher_robot@example.com",
            password="pass1234",
        )
        profile = self.teacher.userprofile
        profile.status = UserProfile.ROLE_PROFESSOR
        profile.save(update_fields=["status"])

        self.student = User.objects.create_user(
            username="student_basic",
            email="student_basic@example.com",
            password="pass1234",
        )

    def test_teacher_view_requires_teacher_or_admin(self):
        url = reverse("estudy:robot_lab_teacher")

        self.client.login(username="student_basic", password="pass1234")
        student_response = self.client.get(url)
        self.assertEqual(student_response.status_code, 403)

        self.client.logout()
        self.client.login(username="teacher_robot", password="pass1234")
        teacher_response = self.client.get(url)
        self.assertEqual(teacher_response.status_code, 200)


class RobotLabFeatureFlagOffTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="flag_off_user",
            email="flag_off_user@example.com",
            password="pass1234",
        )
        self.client.login(username="flag_off_user", password="pass1234")

    def test_robot_lab_api_hidden_when_feature_off(self):
        response = self.client.get(reverse("estudy:robot_lab_levels_api"))
        self.assertEqual(response.status_code, 404)
