import unittest

try:
    from app.engine import run_student_code
except ModuleNotFoundError:
    from runner_service.app.engine import run_student_code

TEST_LEVEL = {
    "id": "T-01",
    "goal": {"type": "reach_goal"},
    "grid": [
        "#####",
        "#S.G#",
        "#####",
    ],
    "start_dir": "E",
}


class RunnerEngineTests(unittest.TestCase):
    def test_cardinal_command_success(self):
        result = run_student_code(
            level_id="T-01",
            student_code="right()\nright()",
            level_spec=TEST_LEVEL,
            allowed_api=["right", "left", "up", "down", "at_goal"],
            max_steps=20,
        )
        self.assertEqual(result["error_type"], "none")
        self.assertEqual(result["steps_used"], 2)
        self.assertEqual(result["optimal_steps"], 2)

    def test_reach_goal_success(self):
        result = run_student_code(
            level_id="T-01",
            student_code="move()\nmove()",
            level_spec=TEST_LEVEL,
            allowed_api=["move", "at_goal", "turn_left", "turn_right"],
            max_steps=20,
        )
        self.assertEqual(result["error_type"], "none")
        self.assertTrue(result["steps_used"] >= 2)

    def test_ast_import_blocked(self):
        result = run_student_code(
            level_id="T-01",
            student_code="import os\nmove()",
            level_spec=TEST_LEVEL,
            allowed_api=["move", "at_goal"],
            max_steps=20,
        )
        self.assertEqual(result["error_type"], "syntax")

    def test_unknown_command_returns_suggestion(self):
        result = run_student_code(
            level_id="T-01",
            student_code="rigth()",
            level_spec=TEST_LEVEL,
            allowed_api=["right", "left", "up", "down"],
            max_steps=20,
        )
        self.assertEqual(result["error_type"], "syntax")
        self.assertEqual(result["primary_error"], "unknown_command:rigth:right")

    def test_hit_wall_runtime(self):
        result = run_student_code(
            level_id="T-01",
            student_code="turn_left()\nmove()",
            level_spec=TEST_LEVEL,
            allowed_api=["move", "turn_left"],
            max_steps=20,
        )
        self.assertEqual(result["error_type"], "runtime")
        self.assertEqual(result["primary_error"], "hit_wall")


if __name__ == "__main__":
    unittest.main()
