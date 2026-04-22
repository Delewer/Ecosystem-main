import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import RobotLabAttemptLog, RobotLabSkillProfile


class RobotLabMentorApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="robotkid",
            email="robotkid@example.com",
            password="pass1234",
        )
        self.client.login(username="robotkid", password="pass1234")
        self.url = reverse("estudy:robot_lab_mentor_api")

    def _post(self, payload):
        return self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_returns_strict_required_keys_without_solution_by_default(self):
        payload = {
            "level_id": "W3-L02",
            "goal": "Reach the goal",
            "concepts": ["condition"],
            "student_code": "move()\nmove()\nmove()",
            "execution_trace": [
                {"step": 1, "action": "move", "position": [1, 2], "dir": "E"},
                {"step": 2, "action": "move", "position": [1, 3], "dir": "E"},
                {"step": 3, "error": "hit_wall", "position": [1, 3], "dir": "E"},
            ],
            "error_type": "runtime",
            "attempt_number": 1,
            "student_requested_solution": False,
            "level_metadata": {
                "allowed_api": [
                    "move",
                    "turn_left",
                    "turn_right",
                    "front_is_clear",
                    "at_goal",
                ]
            },
        }

        response = self._post(payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        expected_keys = {
            "what_happened",
            "mistake_explanation",
            "hint_level_1",
            "hint_level_2",
            "concept_focus",
            "encouragement",
        }
        self.assertEqual(set(data.keys()), expected_keys)
        self.assertEqual(data["concept_focus"], "condition")
        self.assertEqual(RobotLabAttemptLog.objects.filter(user=self.user).count(), 1)
        self.assertTrue(RobotLabSkillProfile.objects.filter(user=self.user).exists())

    def test_requires_authenticated_user(self):
        self.client.logout()
        response = self._post({"level_id": "W1-L01"})
        self.assertEqual(response.status_code, 403)

    def test_adds_example_solution_only_when_requested(self):
        payload = {
            "level_id": "W1-L03",
            "goal": "Reach the goal",
            "concepts": ["sequencing"],
            "student_code": "move()",
            "execution_trace": [],
            "error_type": "logic",
            "attempt_number": 3,
            "student_requested_solution": True,
        }

        response = self._post(payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        expected_keys = {
            "what_happened",
            "mistake_explanation",
            "hint_level_1",
            "hint_level_2",
            "concept_focus",
            "encouragement",
            "example_solution",
        }
        self.assertEqual(set(data.keys()), expected_keys)
        self.assertTrue(data["example_solution"])

        last_attempt = RobotLabAttemptLog.objects.filter(user=self.user).latest("id")
        self.assertTrue(last_attempt.requested_solution)

    def test_updates_skill_profile_on_solved_attempt(self):
        payload = {
            "level_id": "W2-L05",
            "goal": "Reach the goal",
            "concepts": ["loop"],
            "student_code": "while not at_goal():\n    move()",
            "execution_trace": [
                {"step": 1, "action": "move"},
                {"step": 2, "action": "move"},
            ],
            "error_type": "none",
            "attempt_number": 2,
            "student_requested_solution": False,
            "history": [
                {"attempt": 1, "error_type": "runtime", "primary_error": "hit_wall"}
            ],
        }

        response = self._post(payload)
        self.assertEqual(response.status_code, 200)

        profile = RobotLabSkillProfile.objects.get(user=self.user)
        self.assertEqual(profile.loop_score, 5)
        self.assertEqual(profile.debugging_score, 3)
