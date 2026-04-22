from __future__ import annotations

import json
import time
import uuid
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


class RobotLabRunnerError(RuntimeError):
    pass


class RobotLabRunnerUnavailableError(RobotLabRunnerError):
    pass


def _runner_url() -> str:
    value = str(getattr(settings, "ROBOT_RUNNER_URL", "") or "").strip()
    return value.rstrip("/")


def _local_fallback_enabled() -> bool:
    fallback = getattr(settings, "ROBOT_RUNNER_LOCAL_FALLBACK", None)
    if fallback is None:
        return bool(getattr(settings, "DEBUG", False))
    return bool(fallback)


def _execute_robot_lab_code_locally(
    *,
    level_id: str,
    student_code: str,
    level_spec: dict[str, Any],
    allowed_api: list[str],
    max_steps: int,
) -> dict[str, Any]:
    try:
        from runner_service.app.engine import run_student_code
    except Exception as exc:  # pragma: no cover
        raise RobotLabRunnerUnavailableError(
            "Local runner fallback is unavailable"
        ) from exc

    started = time.perf_counter()
    result = run_student_code(
        level_id=level_id,
        student_code=student_code,
        level_spec=level_spec,
        allowed_api=allowed_api,
        max_steps=max_steps,
    )
    if not isinstance(result, dict):
        raise RobotLabRunnerError("Local runner returned invalid payload format")
    result.setdefault("duration_ms", int((time.perf_counter() - started) * 1000))
    return result


def execute_robot_lab_code(
    *,
    level_id: str,
    student_code: str,
    level_spec: dict[str, Any],
    allowed_api: list[str],
    max_steps: int,
    time_limit_ms: int,
    run_id: str | None = None,
) -> dict[str, Any]:
    runner_url = _runner_url()
    if not runner_url:
        if _local_fallback_enabled():
            return _execute_robot_lab_code_locally(
                level_id=level_id,
                student_code=student_code,
                level_spec=level_spec,
                allowed_api=allowed_api,
                max_steps=max_steps,
            )
        raise RobotLabRunnerUnavailableError("ROBOT_RUNNER_URL is not configured")

    payload = {
        "run_id": run_id or str(uuid.uuid4()),
        "level_id": level_id,
        "student_code": student_code,
        "level_spec": level_spec,
        "allowed_api": allowed_api,
        "max_steps": int(max_steps),
        "time_limit_ms": int(time_limit_ms),
    }
    data = json.dumps(payload).encode("utf-8")
    token = str(getattr(settings, "ROBOT_RUNNER_TOKEN", "") or "").strip()
    timeout_ms = int(getattr(settings, "ROBOT_RUNNER_TIMEOUT_MS", 3000) or 3000)
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(
        url=f"{runner_url}/v1/execute",
        data=data,
        headers=headers,
        method="POST",
    )

    try:
        with urlopen(request, timeout=max(timeout_ms / 1000.0, 0.25)) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise RobotLabRunnerError(f"Runner HTTP {exc.code}: {body[:300]}") from exc
    except URLError as exc:
        raise RobotLabRunnerUnavailableError(
            f"Runner is unreachable: {exc.reason}"
        ) from exc
    except Exception as exc:  # pragma: no cover
        raise RobotLabRunnerError(f"Runner request failed: {exc}") from exc

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RobotLabRunnerError("Runner returned invalid JSON") from exc

    if not isinstance(parsed, dict):
        raise RobotLabRunnerError("Runner returned invalid payload format")
    return parsed
