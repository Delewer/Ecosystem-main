from __future__ import annotations

import multiprocessing as mp
import os
import time
from queue import Empty
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .engine import run_student_code
from .mock_turtle import install as install_mock_turtle

install_mock_turtle()

app = FastAPI(title="Robot Lab Runner", version="1.0.0")


class ExecuteRequest(BaseModel):
    run_id: str
    level_id: str
    student_code: str
    level_spec: dict[str, Any]
    allowed_api: list[str] = Field(default_factory=list)
    max_steps: int = 200
    time_limit_ms: int = 800


def _payload_to_dict(payload: ExecuteRequest) -> dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump()
    return payload.dict()


def _authorized(auth_header: str | None) -> bool:
    expected = str(os.environ.get("ROBOT_RUNNER_TOKEN", "") or "").strip()
    if not expected:
        return True
    incoming = str(auth_header or "").strip()
    return incoming == f"Bearer {expected}"


def _worker(payload: dict[str, Any], queue: mp.Queue) -> None:
    started = time.perf_counter()
    result = run_student_code(
        level_id=str(payload.get("level_id") or ""),
        student_code=str(payload.get("student_code") or ""),
        level_spec=payload.get("level_spec")
        if isinstance(payload.get("level_spec"), dict)
        else {},
        allowed_api=payload.get("allowed_api")
        if isinstance(payload.get("allowed_api"), list)
        else [],
        max_steps=max(1, int(payload.get("max_steps") or 200)),
    )
    result["duration_ms"] = int((time.perf_counter() - started) * 1000)
    queue.put(result)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/execute")
def execute(
    payload: ExecuteRequest, authorization: str | None = Header(default=None)
) -> dict[str, Any]:
    if not _authorized(authorization):
        raise HTTPException(status_code=401, detail="Unauthorized")

    context = mp.get_context("spawn")
    queue: mp.Queue = context.Queue()
    process = context.Process(target=_worker, args=(_payload_to_dict(payload), queue))
    process.start()

    timeout_s = max(0.1, int(payload.time_limit_ms) / 1000.0)
    process.join(timeout_s)
    if process.is_alive():
        process.terminate()
        process.join(0.2)
        return {
            "status": "error",
            "error_type": "timeout",
            "primary_error": "step_limit_exceeded",
            "execution_trace": [],
            "final_state": {},
            "steps_used": 0,
            "duration_ms": int(timeout_s * 1000),
        }

    try:
        result = queue.get_nowait()
    except Empty:
        return {
            "status": "error",
            "error_type": "runtime",
            "primary_error": "invalid_action",
            "execution_trace": [],
            "final_state": {},
            "steps_used": 0,
            "duration_ms": 0,
        }

    if not isinstance(result, dict):
        return {
            "status": "error",
            "error_type": "runtime",
            "primary_error": "invalid_action",
            "execution_trace": [],
            "final_state": {},
            "steps_used": 0,
            "duration_ms": 0,
        }
    result.setdefault("status", "error")
    result.setdefault("error_type", "runtime")
    result.setdefault("primary_error", "invalid_action")
    result.setdefault("execution_trace", [])
    result.setdefault("final_state", {})
    result.setdefault("steps_used", 0)
    result.setdefault("duration_ms", 0)
    return result
