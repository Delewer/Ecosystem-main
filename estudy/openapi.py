from __future__ import annotations

import re

from rest_framework.schemas.openapi import AutoSchema

PATH_TOKEN_RE = re.compile(r"[^0-9A-Za-z]+")


def _camelize_path(path: str) -> str:
    parts = [
        part
        for part in PATH_TOKEN_RE.split(path.replace("{", "").replace("}", ""))
        if part
    ]
    return "".join(part[:1].upper() + part[1:] for part in parts)


class UniqueOperationIdAutoSchema(AutoSchema):
    """Make DRF operationIds stable and unique across versioned API prefixes."""

    def get_operation_id(self, path: str, method: str) -> str:
        base_operation_id = super().get_operation_id(path, method)
        path_suffix = _camelize_path(path.strip("/"))
        if not path_suffix:
            return base_operation_id
        return f"{base_operation_id}{path_suffix}"
