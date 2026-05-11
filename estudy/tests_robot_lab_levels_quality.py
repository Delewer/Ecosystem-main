from __future__ import annotations

from collections import deque

from django.test import SimpleTestCase

from runner_service.app.engine import (
    MUTATING_ACTIONS,
    _apply_search_action,
    _compute_optimal_steps,
    _find_start,
    _find_tiles,
    _goal_reached,
    _goal_tiles,
    _grid_rows,
    _item_positions,
    run_student_code,
)

from .services.robot_lab_levels import load_level, ordered_level_ids
from .services.robot_lab_progress import _compute_stars


def _shortest_command_path(level_spec):
    grid = _grid_rows(level_spec)
    if not grid:
        return None

    allowed = [
        str(item).strip()
        for item in (level_spec.get("allowed_api") or [])
        if str(item).strip()
    ]
    actions = [action for action in allowed if action in MUTATING_ACTIONS]
    if not actions:
        return None

    start = _find_start(level_spec, grid)
    goal_positions = _find_tiles(grid, _goal_tiles(level_spec))
    terminal_positions = _find_tiles(grid, ("T",))
    item_positions = _item_positions(grid)
    queue = deque([(start, [])])
    seen = {start}

    while queue:
        state, path = queue.popleft()
        if _goal_reached(level_spec, state, goal_positions):
            return path
        for action in actions:
            next_state = _apply_search_action(
                grid=grid,
                goal_positions=goal_positions,
                terminal_positions=terminal_positions,
                item_positions=item_positions,
                state=state,
                action=action,
            )
            if next_state is None or next_state in seen:
                continue
            seen.add(next_state)
            queue.append((next_state, path + [action]))
    return None


def _step_threshold(condition: str) -> int | None:
    if not condition.startswith("steps_lte_"):
        return None
    try:
        return int(condition.rsplit("_", 1)[-1])
    except ValueError:
        return None


class RobotLabLevelQualityTests(SimpleTestCase):
    def test_all_robot_lab_levels_are_solvable_by_runner(self):
        for level_id in ordered_level_ids():
            with self.subTest(level_id=level_id):
                level = load_level(level_id)
                path = _shortest_command_path(level)
                self.assertIsNotNone(path)
                code = "\n".join(f"{command}()" for command in path)
                result = run_student_code(
                    level_id=level_id,
                    student_code=code,
                    level_spec=level,
                    allowed_api=list(level.get("allowed_api") or []),
                    max_steps=int(level.get("max_steps") or 200),
                )
                self.assertEqual(result["error_type"], "none")
                self.assertEqual(result["steps_used"], len(path))

    def test_level_optimal_steps_match_runner_and_star_thresholds(self):
        for level_id in ordered_level_ids():
            with self.subTest(level_id=level_id):
                level = load_level(level_id)
                optimal_steps = _compute_optimal_steps(
                    level, set(level.get("allowed_api") or [])
                )
                self.assertIsNotNone(optimal_steps)
                self.assertEqual(int(level.get("optimal_steps") or 0), optimal_steps)

                threshold = _step_threshold(
                    str((level.get("star_conditions") or {}).get("two") or "")
                )
                if threshold is not None:
                    self.assertGreaterEqual(threshold, optimal_steps)

    def test_visual_button_levels_have_enough_slots_for_shortest_path(self):
        for level_id in ordered_level_ids():
            level = load_level(level_id)
            if level.get("ui_stage") not in {"buttons", "buttons_code"}:
                continue
            with self.subTest(level_id=level_id):
                optimal_steps = int(level.get("optimal_steps") or 0)
                max_sequence_length = int(level.get("max_sequence_length") or 12)
                self.assertGreaterEqual(max_sequence_length, optimal_steps)

    def test_solved_activate_levels_still_earn_first_star(self):
        stars = _compute_stars(
            level_spec={
                "star_conditions": {
                    "one": "reach_goal",
                    "two": "steps_lte_40",
                    "three": "steps_lte_optimal",
                }
            },
            solved=True,
            steps_used=50,
            optimal_steps=27,
        )

        self.assertEqual(stars, 1)
