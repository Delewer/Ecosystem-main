from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

DEFAULT_ERROR_MESSAGE = "Service call failed"
EMPTY_DATA: dict[str, Any] = {}
EMPTY_META: dict[str, Any] = {}


def _normalize_warnings(warnings: Iterable[str] | None) -> tuple[str, ...]:
    if warnings is None:
        return tuple()
    return tuple(str(item) for item in warnings if str(item).strip())


@dataclass(frozen=True)
class BaseServiceResult:
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    warnings: tuple[str, ...] = field(default_factory=tuple)
    meta: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(
        cls,
        *,
        data: dict[str, Any] | None = None,
        warnings: Iterable[str] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> "BaseServiceResult":
        return cls(
            success=True,
            data=dict(data or EMPTY_DATA),
            warnings=_normalize_warnings(warnings),
            meta=dict(meta or EMPTY_META),
        )

    @classmethod
    def fail(
        cls,
        error: str,
        *,
        data: dict[str, Any] | None = None,
        warnings: Iterable[str] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> "BaseServiceResult":
        return cls(
            success=False,
            data=dict(data or EMPTY_DATA),
            error=str(error),
            warnings=_normalize_warnings(warnings),
            meta=dict(meta or EMPTY_META),
        )

    def require_success(self) -> "BaseServiceResult":
        if not self.success:
            message = self.error or DEFAULT_ERROR_MESSAGE
            raise ValueError(message)
        return self
