from __future__ import annotations

import ast
import difflib
import io
import re
import sys
from collections import deque
from dataclasses import dataclass
from typing import Any

SAFE_BUILTINS = {
    "range": range,
    "len": len,
    "min": min,
    "max": max,
    "abs": abs,
    "int": int,
    "float": float,
    "bool": bool,
}

FORBIDDEN_NODES = (
    ast.Import,
    ast.ImportFrom,
    ast.With,
    ast.Try,
    ast.Raise,
    ast.Lambda,
    ast.ClassDef,
    ast.Global,
    ast.Nonlocal,
    ast.AsyncFor,
    ast.AsyncFunctionDef,
    ast.AsyncWith,
    ast.Await,
    ast.Yield,
    ast.YieldFrom,
)

MUTATING_ACTIONS = {
    "up",
    "down",
    "left",
    "right",
    "move",
    "turn_left",
    "turn_right",
    "pick",
    "activate",
}
CARDINAL_DELTAS = {
    "up": (-1, 0, "N"),
    "down": (1, 0, "S"),
    "left": (0, -1, "W"),
    "right": (0, 1, "E"),
}
TURN_LEFT = {"N": "W", "W": "S", "S": "E", "E": "N"}
TURN_RIGHT = {"N": "E", "E": "S", "S": "W", "W": "N"}
NAME_ERROR_PATTERN = re.compile(r"name '([^']+)' is not defined")


class RobotRuntimeError(RuntimeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class StepLimitExceeded(RobotRuntimeError):
    def __init__(self):
        super().__init__("step_limit_exceeded")


@dataclass
class RobotState:
    row: int
    col: int
    direction: str = "E"


@dataclass(frozen=True)
class SearchState:
    row: int
    col: int
    direction: str
    inventory: tuple[str, ...] = ()
    picked_positions: tuple[tuple[int, int], ...] = ()
    terminal_activated: bool = False


def _grid_rows(level_spec: dict[str, Any]) -> list[list[str]]:
    return [list(str(row)) for row in (level_spec.get("grid") or [])]


def _normalize_direction(value: Any) -> str:
    direction = str(value or "E").upper()
    return direction if direction in {"N", "E", "S", "W"} else "E"


def _goal_tiles(level_spec: dict[str, Any]) -> tuple[str, ...]:
    goal = level_spec.get("goal") or {}
    explicit_tiles = goal.get("target_tiles")
    if isinstance(explicit_tiles, list):
        normalized = [
            str(item).strip().upper() for item in explicit_tiles if str(item).strip()
        ]
        if normalized:
            return tuple(normalized)
    explicit_tile = str(goal.get("target_tile") or "").strip().upper()
    if explicit_tile:
        return (explicit_tile,)
    return ("G",)


def _find_tiles(
    grid: list[list[str]], targets: tuple[str, ...]
) -> set[tuple[int, int]]:
    found: set[tuple[int, int]] = set()
    target_set = set(targets)
    for row_index, row in enumerate(grid):
        for col_index, tile in enumerate(row):
            if tile in target_set:
                found.add((row_index, col_index))
    return found


def _find_start(level_spec: dict[str, Any], grid: list[list[str]]) -> SearchState:
    for row_index, row in enumerate(grid):
        for col_index, tile in enumerate(row):
            if tile == "S":
                return SearchState(
                    row=row_index,
                    col=col_index,
                    direction=_normalize_direction(level_spec.get("start_dir")),
                )
    return SearchState(row=0, col=0, direction="E")


def _item_positions(grid: list[list[str]]) -> dict[tuple[int, int], str]:
    mapping: dict[tuple[int, int], str] = {}
    item_by_tile = {"B": "battery", "K": "key"}
    for row_index, row in enumerate(grid):
        for col_index, tile in enumerate(row):
            item_name = item_by_tile.get(tile)
            if item_name:
                mapping[(row_index, col_index)] = item_name
    return mapping


def _tile_at(grid: list[list[str]], row: int, col: int) -> str:
    if row < 0 or col < 0 or row >= len(grid):
        return "#"
    row_data = grid[row]
    if col >= len(row_data):
        return "#"
    return row_data[col]


def _is_walkable(tile: str, inventory: tuple[str, ...]) -> bool:
    if tile == "#":
        return False
    if tile == "D":
        return "key" in inventory
    return True


def _near_terminal(
    row: int, col: int, terminal_positions: set[tuple[int, int]]
) -> bool:
    for terminal_row, terminal_col in terminal_positions:
        if abs(terminal_row - row) + abs(terminal_col - col) <= 1:
            return True
    return False


def _goal_reached(
    level_spec: dict[str, Any],
    state: SearchState,
    goal_positions: set[tuple[int, int]],
) -> bool:
    goal = level_spec.get("goal") or {}
    goal_type = str(goal.get("type") or "reach_goal")
    at_goal = (state.row, state.col) in goal_positions
    if goal_type == "reach_goal":
        return at_goal
    if goal_type == "activate_terminal":
        return state.terminal_activated
    if goal_type == "deliver_item":
        item = str(goal.get("item") or "").strip().lower()
        if item and item not in state.inventory:
            return False
        return at_goal
    return at_goal


def _apply_search_action(
    *,
    grid: list[list[str]],
    goal_positions: set[tuple[int, int]],
    terminal_positions: set[tuple[int, int]],
    item_positions: dict[tuple[int, int], str],
    state: SearchState,
    action: str,
) -> SearchState | None:
    if action in CARDINAL_DELTAS:
        delta_row, delta_col, direction = CARDINAL_DELTAS[action]
        next_row = state.row + delta_row
        next_col = state.col + delta_col
        tile = _tile_at(grid, next_row, next_col)
        if not _is_walkable(tile, state.inventory):
            return None
        return SearchState(
            row=next_row,
            col=next_col,
            direction=direction,
            inventory=state.inventory,
            picked_positions=state.picked_positions,
            terminal_activated=state.terminal_activated,
        )

    if action == "move":
        delta_row, delta_col = {
            "N": (-1, 0),
            "E": (0, 1),
            "S": (1, 0),
            "W": (0, -1),
        }[state.direction]
        next_row = state.row + delta_row
        next_col = state.col + delta_col
        tile = _tile_at(grid, next_row, next_col)
        if not _is_walkable(tile, state.inventory):
            return None
        return SearchState(
            row=next_row,
            col=next_col,
            direction=state.direction,
            inventory=state.inventory,
            picked_positions=state.picked_positions,
            terminal_activated=state.terminal_activated,
        )

    if action == "turn_left":
        return SearchState(
            row=state.row,
            col=state.col,
            direction=TURN_LEFT[state.direction],
            inventory=state.inventory,
            picked_positions=state.picked_positions,
            terminal_activated=state.terminal_activated,
        )

    if action == "turn_right":
        return SearchState(
            row=state.row,
            col=state.col,
            direction=TURN_RIGHT[state.direction],
            inventory=state.inventory,
            picked_positions=state.picked_positions,
            terminal_activated=state.terminal_activated,
        )

    if action == "pick":
        current_position = (state.row, state.col)
        if current_position in state.picked_positions:
            return None
        item_name = item_positions.get(current_position)
        if not item_name:
            return None
        next_inventory = tuple(sorted(set(state.inventory) | {item_name}))
        next_picked = tuple(sorted(set(state.picked_positions) | {current_position}))
        return SearchState(
            row=state.row,
            col=state.col,
            direction=state.direction,
            inventory=next_inventory,
            picked_positions=next_picked,
            terminal_activated=state.terminal_activated,
        )

    if action == "activate":
        if not _near_terminal(state.row, state.col, terminal_positions):
            return None
        return SearchState(
            row=state.row,
            col=state.col,
            direction=state.direction,
            inventory=state.inventory,
            picked_positions=state.picked_positions,
            terminal_activated=True,
        )

    return None


def _compute_optimal_steps(
    level_spec: dict[str, Any], allowed_api: set[str]
) -> int | None:
    grid = _grid_rows(level_spec)
    if not grid:
        return None

    start_state = _find_start(level_spec, grid)
    item_positions = _item_positions(grid)
    goal_positions = _find_tiles(grid, _goal_tiles(level_spec))
    terminal_positions = _find_tiles(grid, ("T",))
    actions = [action for action in allowed_api if action in MUTATING_ACTIONS]
    if not actions:
        return None

    queue: deque[tuple[SearchState, int]] = deque([(start_state, 0)])
    seen: set[SearchState] = {start_state}

    while queue:
        state, distance = queue.popleft()
        if _goal_reached(level_spec, state, goal_positions):
            return distance
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
            queue.append((next_state, distance + 1))
    return None


def _normalize_python_syntax_error(exc: SyntaxError) -> str:
    message = str(getattr(exc, "msg", "") or str(exc)).strip().lower()
    if "indent" in message:
        return "indentation_error"
    return "syntax_error"


def _suggest_command(name: str, allowed_api: set[str]) -> str:
    matches = difflib.get_close_matches(name, sorted(allowed_api), n=1, cutoff=0.6)
    return matches[0] if matches else ""


class RobotWorld:
    DIRECTIONS = ["N", "E", "S", "W"]
    DELTAS = {
        "N": (-1, 0),
        "E": (0, 1),
        "S": (1, 0),
        "W": (0, -1),
    }
    ITEM_BY_TILE = {"B": "battery", "K": "key"}

    def __init__(self, *, level_spec: dict[str, Any], max_steps: int):
        self.level_spec = level_spec
        self.grid = _grid_rows(level_spec)
        self.rows = len(self.grid)
        self.cols = len(self.grid[0]) if self.rows else 0
        self.max_steps = max(1, int(max_steps))
        start = _find_start(level_spec, self.grid)
        self.state = RobotState(row=start.row, col=start.col, direction=start.direction)
        self.goal_positions = _find_tiles(self.grid, _goal_tiles(level_spec))
        self.terminal_positions = _find_tiles(self.grid, ("T",))
        self.trace: list[dict[str, Any]] = []
        self.steps = 0
        self.inventory: set[str] = set()
        self.terminal_activated = False

    def _tile(self, row: int, col: int) -> str:
        return _tile_at(self.grid, row, col)

    def _front(self) -> tuple[int, int]:
        delta_row, delta_col = self.DELTAS[self.state.direction]
        return self.state.row + delta_row, self.state.col + delta_col

    def _is_walkable(self, tile: str) -> bool:
        return _is_walkable(tile, tuple(sorted(self.inventory)))

    def _add_trace(self, action: str, *, error: str = "") -> None:
        if self.steps >= self.max_steps:
            raise StepLimitExceeded()
        self.steps += 1
        item: dict[str, Any] = {
            "step": self.steps,
            "action": action,
            "position": [self.state.row, self.state.col],
            "dir": self.state.direction,
        }
        if error:
            item["error"] = error
        self.trace.append(item)

    def _move_to(self, *, direction: str, action: str) -> None:
        self.state.direction = direction
        delta_row, delta_col = self.DELTAS[direction]
        next_row = self.state.row + delta_row
        next_col = self.state.col + delta_col
        tile = self._tile(next_row, next_col)
        if not self._is_walkable(tile):
            self._add_trace(action, error="hit_wall")
            raise RobotRuntimeError("hit_wall")
        self.state.row, self.state.col = next_row, next_col
        self._add_trace(action)
        if tile == "H":
            self.trace[-1]["error"] = "stepped_on_hazard"
            raise RobotRuntimeError("stepped_on_hazard")

    def move(self) -> None:
        self._move_to(direction=self.state.direction, action="move")

    def up(self) -> None:
        self._move_to(direction="N", action="up")

    def down(self) -> None:
        self._move_to(direction="S", action="down")

    def left(self) -> None:
        self._move_to(direction="W", action="left")

    def right(self) -> None:
        self._move_to(direction="E", action="right")

    def turn_left(self) -> None:
        self.state.direction = TURN_LEFT[self.state.direction]
        self._add_trace("turn_left")

    def turn_right(self) -> None:
        self.state.direction = TURN_RIGHT[self.state.direction]
        self._add_trace("turn_right")

    def pick(self) -> None:
        tile = self._tile(self.state.row, self.state.col)
        item_name = self.ITEM_BY_TILE.get(tile)
        if not item_name:
            self._add_trace("pick", error="no_item_to_pick")
            raise RobotRuntimeError("no_item_to_pick")
        self.inventory.add(item_name)
        self.grid[self.state.row][self.state.col] = "."
        self._add_trace("pick")

    def activate(self) -> None:
        if not self.near_terminal():
            self._add_trace("activate", error="cannot_activate")
            raise RobotRuntimeError("cannot_activate")
        self.terminal_activated = True
        self._add_trace("activate")

    def front_is_clear(self) -> bool:
        next_row, next_col = self._front()
        return self._is_walkable(self._tile(next_row, next_col))

    def at_goal(self) -> bool:
        return (self.state.row, self.state.col) in self.goal_positions

    def on_item(self) -> bool:
        return self._tile(self.state.row, self.state.col) in self.ITEM_BY_TILE

    def near_terminal(self) -> bool:
        return _near_terminal(self.state.row, self.state.col, self.terminal_positions)

    def has_item(self, name: str) -> bool:
        return str(name) in self.inventory

    def final_state(self) -> dict[str, Any]:
        return {
            "position": [self.state.row, self.state.col],
            "direction": self.state.direction,
            "inventory": sorted(self.inventory),
            "terminal_activated": self.terminal_activated,
            "at_goal": self.at_goal(),
        }

    def goal_result(self) -> tuple[bool, str]:
        goal = self.level_spec.get("goal") or {}
        goal_type = str(goal.get("type") or "reach_goal")
        if goal_type == "reach_goal":
            if self.at_goal():
                return True, ""
            return False, "not_reached_goal"
        if goal_type == "activate_terminal":
            if self.terminal_activated:
                return True, ""
            return False, "missing_activate"
        if goal_type == "deliver_item":
            item = str(goal.get("item") or "").strip().lower()
            if item and item not in self.inventory:
                return False, "missing_pick"
            if not self.at_goal():
                return False, "wrong_delivery"
            return True, ""
        return (self.at_goal(), "" if self.at_goal() else "not_reached_goal")


def validate_code_ast(code: str, allowed_api: set[str]) -> None:
    source = code or ""
    if len(source) > 10000:
        raise SyntaxError("code_too_long")
    if "___" in source:
        raise SyntaxError("missing_command_placeholder")

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise SyntaxError(_normalize_python_syntax_error(exc)) from exc

    for node in ast.walk(tree):
        if isinstance(node, FORBIDDEN_NODES):
            raise SyntaxError(f"forbidden_syntax:{type(node).__name__}")
        if isinstance(node, ast.Attribute):
            raise SyntaxError("forbidden_attribute_access")
        if isinstance(node, ast.Name) and str(node.id).startswith("__"):
            raise SyntaxError("forbidden_identifier")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise SyntaxError("forbidden_call_shape")
            function_name = str(node.func.id)
            if function_name not in allowed_api and function_name not in SAFE_BUILTINS:
                suggestion = _suggest_command(function_name, allowed_api)
                if suggestion:
                    raise SyntaxError(f"unknown_command:{function_name}:{suggestion}")
                raise SyntaxError(f"unknown_command:{function_name}")


def _check_turtle_goal(
    turtle_lines: list[str], level_spec: dict[str, Any]
) -> tuple[bool, str]:
    """Check if turtle output satisfies the level's turtle_draw goal."""
    goal = level_spec.get("goal") or {}
    if str(goal.get("type") or "") != "turtle_draw":
        return False, "not_turtle_goal"
    if not turtle_lines:
        return False, "no_turtle_output"
    target = str(goal.get("target_shape") or "").lower()
    if target == "square":
        fwd_count = sum(
            1 for line in turtle_lines if line.startswith("TURTLE:forward:")
        )
        turn_count = sum(
            1
            for line in turtle_lines
            if line.startswith("TURTLE:right:90") or line.startswith("TURTLE:left:90")
        )
        if fwd_count >= 4 and turn_count >= 4:
            return True, ""
        return False, "incomplete_shape"
    # Generic turtle goal: any output counts as success
    return True, ""


def run_student_code(
    *,
    level_id: str,
    student_code: str,
    level_spec: dict[str, Any],
    allowed_api: list[str],
    max_steps: int,
) -> dict[str, Any]:
    allowed = {str(item).strip() for item in (allowed_api or []) if str(item).strip()}
    optimal_steps = _compute_optimal_steps(level_spec, allowed)
    turtle_enabled = bool(level_spec.get("turtle_enabled"))

    try:
        validate_code_ast(student_code, allowed)
    except SyntaxError as exc:
        return {
            "status": "error",
            "error_type": "syntax",
            "primary_error": str(exc),
            "execution_trace": [],
            "final_state": {},
            "steps_used": 0,
            "optimal_steps": optimal_steps,
        }

    world = RobotWorld(level_spec=level_spec, max_steps=max_steps)
    globals_scope = {
        "__builtins__": SAFE_BUILTINS,
        "up": world.up,
        "down": world.down,
        "left": world.left,
        "right": world.right,
        "move": world.move,
        "turn_left": world.turn_left,
        "turn_right": world.turn_right,
        "pick": world.pick,
        "activate": world.activate,
        "front_is_clear": world.front_is_clear,
        "at_goal": world.at_goal,
        "on_item": world.on_item,
        "near_terminal": world.near_terminal,
        "has_item": world.has_item,
    }

    if turtle_enabled:
        from .mock_turtle import _MockTurtle

        _t = _MockTurtle()
        globals_scope.update(
            {
                "forward": _t.forward,
                "fd": _t.fd,
                "backward": _t.backward,
                "right": _t.right,
                "left": _t.left,
                "penup": _t.penup,
                "pendown": _t.pendown,
                "color": _t.color,
                "goto": _t.goto,
            }
        )

    stdout_capture = io.StringIO()
    result = None

    _real_stdout = sys.stdout
    sys.stdout = stdout_capture
    try:
        try:
            compiled = compile(student_code, f"<robot-lab:{level_id}>", "exec")
            exec(compiled, globals_scope, {})
        except StepLimitExceeded as exc:
            result = {
                "status": "error",
                "error_type": "timeout",
                "primary_error": exc.code,
                "execution_trace": world.trace,
                "final_state": world.final_state(),
                "steps_used": world.steps,
                "optimal_steps": optimal_steps,
            }
        except RobotRuntimeError as exc:
            result = {
                "status": "error",
                "error_type": "runtime",
                "primary_error": exc.code,
                "execution_trace": world.trace,
                "final_state": world.final_state(),
                "steps_used": world.steps,
                "optimal_steps": optimal_steps,
            }
        except NameError as exc:
            match = NAME_ERROR_PATTERN.search(str(exc))
            missing_name = match.group(1) if match else "unknown"
            suggestion = _suggest_command(missing_name, allowed)
            primary_error = f"unknown_command:{missing_name}"
            if suggestion:
                primary_error = f"{primary_error}:{suggestion}"
            result = {
                "status": "error",
                "error_type": "syntax",
                "primary_error": primary_error,
                "execution_trace": world.trace,
                "final_state": world.final_state(),
                "steps_used": world.steps,
                "optimal_steps": optimal_steps,
            }
        except SyntaxError as exc:
            result = {
                "status": "error",
                "error_type": "syntax",
                "primary_error": _normalize_python_syntax_error(exc),
                "execution_trace": world.trace,
                "final_state": world.final_state(),
                "steps_used": world.steps,
                "optimal_steps": optimal_steps,
            }
        except Exception as exc:  # pragma: no cover
            result = {
                "status": "error",
                "error_type": "runtime",
                "primary_error": f"invalid_action:{exc.__class__.__name__}",
                "execution_trace": world.trace,
                "final_state": world.final_state(),
                "steps_used": world.steps,
                "optimal_steps": optimal_steps,
            }
    finally:
        sys.stdout = _real_stdout

    captured = stdout_capture.getvalue()
    all_lines = (
        [line for line in captured.split("\n") if line.strip()]
        if captured.strip()
        else []
    )
    turtle_lines = [line for line in all_lines if line.startswith("TURTLE:")]
    stdout_lines = [line for line in all_lines if not line.startswith("TURTLE:")]

    if result is not None:
        result["turtle_output"] = turtle_lines
        result["stdout_lines"] = stdout_lines
        return result

    # Normal completion — check goal
    if turtle_enabled:
        solved, primary_error = _check_turtle_goal(turtle_lines, level_spec)
    else:
        solved, primary_error = world.goal_result()

    if solved:
        return {
            "status": "ok",
            "error_type": "none",
            "primary_error": "",
            "execution_trace": world.trace,
            "final_state": world.final_state(),
            "steps_used": world.steps,
            "optimal_steps": optimal_steps,
            "turtle_output": turtle_lines,
            "stdout_lines": stdout_lines,
        }
    return {
        "status": "error",
        "error_type": "logic",
        "primary_error": primary_error or "not_reached_goal",
        "execution_trace": world.trace,
        "final_state": world.final_state(),
        "steps_used": world.steps,
        "optimal_steps": optimal_steps,
        "turtle_output": turtle_lines,
        "stdout_lines": stdout_lines,
    }
