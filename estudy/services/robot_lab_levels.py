from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

LEVELS_ROOT = Path(__file__).resolve().parents[1] / "robot_lab" / "levels"
LEVELS_INDEX = LEVELS_ROOT / "index.json"
ROBOT_LAB_MODE_LABELS = {
    "junior": "Mod Junior",
    "code": "Mod Cod",
}
ROBOT_LAB_STAGE_LABELS = {
    "buttons": "Butoane vizuale",
    "buttons_code": "Butoane + cod",
    "fill_gaps": "Cod ghidat",
    "code": "Cod complet",
}
ROBOT_LAB_STAGE_DESCRIPTIONS = {
    "buttons": "Apasa butoanele mari ca sa construiesti ruta pas cu pas.",
    "buttons_code": "Construieste traseul cu butoane si observa cum apare codul Python.",
    "fill_gaps": "Completeaza comanda lipsa direct in editor si ruleaza programul.",
    "code": "Scrie singur programul complet si corecteaza-l cu ajutorul consolei.",
}
ROBOT_LAB_CONCEPT_LABELS = {
    "sequencing": "ordine de pasi",
    "debugging": "depanare",
    "logic": "logica",
    "functions": "functii",
}
ROBOT_LAB_DIFFICULTY_LABELS = {
    "easy": "usor",
    "medium": "mediu",
    "hard": "greu",
}


class RobotLabLevelNotFoundError(KeyError):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid JSON object in {path}")
    return data


def _normalize_level_metadata(level: dict[str, Any]) -> dict[str, Any]:
    data = dict(level)
    mode = str(data.get("mode") or "code").strip().lower()
    if mode not in ROBOT_LAB_MODE_LABELS:
        mode = "code"

    stage = str(data.get("ui_stage") or "").strip().lower()
    if stage not in ROBOT_LAB_STAGE_LABELS:
        stage = "buttons" if mode == "junior" else "code"

    data["mode"] = mode
    data["mode_label"] = ROBOT_LAB_MODE_LABELS[mode]
    data["ui_stage"] = stage
    data["ui_stage_label"] = ROBOT_LAB_STAGE_LABELS[stage]
    data["ui_stage_description"] = str(
        data.get("ui_stage_description") or ROBOT_LAB_STAGE_DESCRIPTIONS[stage]
    )
    raw_concepts = data.get("concepts") or []
    if not isinstance(raw_concepts, list):
        raw_concepts = []
    concepts = [str(item).strip() for item in raw_concepts if str(item).strip()]
    data["concepts"] = concepts
    data["concept_labels"] = [
        ROBOT_LAB_CONCEPT_LABELS.get(item, item.replace("_", " ")) for item in concepts
    ]
    difficulty = str(data.get("difficulty") or "easy").strip().lower()
    data["difficulty"] = difficulty
    data["difficulty_label"] = ROBOT_LAB_DIFFICULTY_LABELS.get(difficulty, difficulty)
    data["recommended_age"] = str(
        data.get("recommended_age") or ("8-10" if mode == "junior" else "11+")
    )
    return data


@lru_cache(maxsize=1)
def load_levels_index() -> dict[str, Any]:
    if not LEVELS_INDEX.exists():
        raise FileNotFoundError(f"Robot Lab levels index not found: {LEVELS_INDEX}")
    data = _read_json(LEVELS_INDEX)
    levels = data.get("levels")
    if not isinstance(levels, list):
        raise ValueError("Robot Lab levels index must contain a 'levels' list")
    return data


@lru_cache(maxsize=128)
def load_level(level_id: str) -> dict[str, Any]:
    level = get_level_entry(level_id)
    file_name = str(level.get("file") or "").strip()
    if not file_name:
        raise ValueError(f"Level {level_id} is missing file reference")
    path = LEVELS_ROOT / file_name
    if not path.exists():
        raise FileNotFoundError(f"Robot Lab level file not found: {path}")
    data = _read_json(path)
    merged = dict(level)
    merged.update(data)
    merged.setdefault("id", level_id)
    return _normalize_level_metadata(merged)


def list_level_entries() -> list[dict[str, Any]]:
    index = load_levels_index()
    items = []
    for raw in index.get("levels", []):
        if not isinstance(raw, dict):
            continue
        if not raw.get("id"):
            continue
        items.append(_normalize_level_metadata(dict(raw)))
    items.sort(key=lambda x: (int(x.get("world", 0)), int(x.get("order", 0))))
    return items


def ordered_level_ids() -> list[str]:
    return [str(item["id"]) for item in list_level_entries()]


def get_level_entry(level_id: str) -> dict[str, Any]:
    target = str(level_id or "").strip()
    for item in list_level_entries():
        if str(item.get("id")) == target:
            return item
    raise RobotLabLevelNotFoundError(target)


def next_level_id(level_id: str) -> str | None:
    level_ids = ordered_level_ids()
    try:
        idx = level_ids.index(str(level_id))
    except ValueError:
        return None
    nxt = idx + 1
    if nxt >= len(level_ids):
        return None
    return level_ids[nxt]


def level_map_size(level_spec: dict[str, Any]) -> list[int]:
    grid = level_spec.get("grid") or []
    if not isinstance(grid, list) or not grid:
        return [0, 0]
    width = len(str(grid[0]))
    return [len(grid), width]
