from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from ..models import AuditTrailEntry
from .service_result import BaseServiceResult

DEFAULT_HASH_ALGO = "sha256"
DEFAULT_SOURCE = "app"
DEFAULT_ENCODING = "utf-8"

SUPPORTED_HASH_ALGOS = {DEFAULT_HASH_ALGO}

HASH_SEPARATOR = "|"
EMPTY_PREVIOUS_HASH = ""

NO_ENTRIES_WARNING = "no_entries"
UNKNOWN_HASH_ALGO_WARNING = "unknown_hash_algorithm"

ERROR_RECORD_HASH_MISMATCH = "record_hash_mismatch"
ERROR_PREVIOUS_HASH_MISMATCH = "previous_hash_mismatch"
ERROR_PAYLOAD_HASH_MISMATCH = "payload_hash_mismatch"


@dataclass(frozen=True)
class AuditTrailSnapshot:
    entry_id: int
    record_hash: str
    previous_hash: str | None
    payload_hash: str


def _setting(name: str, default):
    return getattr(settings, name, default)


def _hash_algorithm() -> str:
    value = str(_setting("ESTUDY_AUDIT_TRAIL_HASH_ALGO", DEFAULT_HASH_ALGO)).strip()
    return value or DEFAULT_HASH_ALGO


def _secret() -> str:
    secret = _setting("ESTUDY_AUDIT_TRAIL_SECRET", settings.SECRET_KEY)
    return str(secret or settings.SECRET_KEY)


def _source() -> str:
    source = _setting("ESTUDY_AUDIT_TRAIL_SOURCE", DEFAULT_SOURCE)
    return str(source or DEFAULT_SOURCE)


def _canonical_metadata(metadata: dict | None) -> dict:
    return dict(metadata or {})


def _dump_json(payload: dict) -> str:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def _payload_string(
    event_type: str,
    user_id: int | None,
    created_at,
    metadata: dict,
    source: str,
) -> str:
    return HASH_SEPARATOR.join(
        [
            str(event_type),
            str(user_id or ""),
            created_at.isoformat(),
            str(source),
            _dump_json(metadata),
        ]
    )


def _hash_payload(payload: str, algo: str) -> str:
    if algo not in SUPPORTED_HASH_ALGOS:
        algo = DEFAULT_HASH_ALGO
    digest = hashlib.new(algo)
    digest.update(payload.encode(DEFAULT_ENCODING))
    return digest.hexdigest()


def _hash_record(payload_hash: str, previous_hash: str | None, algo: str) -> str:
    if algo not in SUPPORTED_HASH_ALGOS:
        algo = DEFAULT_HASH_ALGO
    record_input = HASH_SEPARATOR.join(
        [payload_hash, previous_hash or EMPTY_PREVIOUS_HASH, algo]
    )
    return hmac.new(
        _secret().encode(DEFAULT_ENCODING),
        record_input.encode(DEFAULT_ENCODING),
        digestmod=algo,
    ).hexdigest()


def append_audit_entry(
    *,
    event_type: str,
    user=None,
    metadata: dict | None = None,
    created_at=None,
    source: str | None = None,
) -> BaseServiceResult:
    if not event_type:
        return BaseServiceResult.fail("Event type is required")

    created_at = created_at or timezone.now()
    metadata = _canonical_metadata(metadata)

    algo = _hash_algorithm()
    warnings = []
    if algo not in SUPPORTED_HASH_ALGOS:
        warnings.append(UNKNOWN_HASH_ALGO_WARNING)
        algo = DEFAULT_HASH_ALGO

    try:
        with transaction.atomic():
            last_entry = (
                AuditTrailEntry.objects.select_for_update().order_by("-id").first()
            )
            previous_hash = last_entry.record_hash if last_entry else None

            resolved_source = source or _source()
            payload = _payload_string(
                event_type=event_type,
                user_id=getattr(user, "id", None),
                created_at=created_at,
                metadata=metadata,
                source=resolved_source,
            )
            payload_hash = _hash_payload(payload, algo)
            record_hash = _hash_record(payload_hash, previous_hash, algo)

            entry = AuditTrailEntry.objects.create(
                event_type=event_type,
                user=user,
                source=resolved_source,
                hash_algorithm=algo,
                payload_hash=payload_hash,
                previous_hash=previous_hash,
                record_hash=record_hash,
                metadata=metadata,
                created_at=created_at,
            )

            # auto_now_add may override the provided created_at at save time.
            # Recompute hashes from persisted values to keep chain verification stable.
            persisted_payload = _payload_string(
                event_type=entry.event_type,
                user_id=entry.user_id,
                created_at=entry.created_at,
                metadata=_canonical_metadata(entry.metadata),
                source=entry.source,
            )
            persisted_payload_hash = _hash_payload(persisted_payload, algo)
            persisted_record_hash = _hash_record(
                persisted_payload_hash, previous_hash, algo
            )
            if (
                entry.payload_hash != persisted_payload_hash
                or entry.record_hash != persisted_record_hash
            ):
                entry.payload_hash = persisted_payload_hash
                entry.record_hash = persisted_record_hash
                entry.save(update_fields=["payload_hash", "record_hash"])
    except Exception as exc:  # pragma: no cover - defensive fallback
        return BaseServiceResult.fail(
            "Audit trail append failed", meta={"error": str(exc)}
        )

    snapshot = AuditTrailSnapshot(
        entry_id=entry.id,
        record_hash=entry.record_hash,
        previous_hash=entry.previous_hash,
        payload_hash=entry.payload_hash,
    )
    return BaseServiceResult.ok(
        data={"entry": entry, "snapshot": snapshot}, warnings=warnings
    )


def verify_audit_trail() -> BaseServiceResult:
    entries = list(AuditTrailEntry.objects.order_by("id"))
    if not entries:
        return BaseServiceResult.ok(
            data={"valid": True, "checked": 0, "errors": []},
            warnings=[NO_ENTRIES_WARNING],
        )

    errors: list[dict] = []
    previous_hash = None

    for entry in entries:
        payload = _payload_string(
            event_type=entry.event_type,
            user_id=entry.user_id,
            created_at=entry.created_at,
            metadata=_canonical_metadata(entry.metadata),
            source=entry.source,
        )
        expected_payload_hash = _hash_payload(payload, entry.hash_algorithm)
        if entry.payload_hash != expected_payload_hash:
            errors.append(
                {
                    "entry_id": entry.id,
                    "error": ERROR_PAYLOAD_HASH_MISMATCH,
                }
            )

        if entry.previous_hash != previous_hash:
            errors.append(
                {
                    "entry_id": entry.id,
                    "error": ERROR_PREVIOUS_HASH_MISMATCH,
                }
            )

        expected_record_hash = _hash_record(
            expected_payload_hash, previous_hash, entry.hash_algorithm
        )
        if entry.record_hash != expected_record_hash:
            errors.append(
                {
                    "entry_id": entry.id,
                    "error": ERROR_RECORD_HASH_MISMATCH,
                }
            )

        previous_hash = entry.record_hash

    data = {
        "valid": not errors,
        "checked": len(entries),
        "errors": errors,
    }
    if errors:
        return BaseServiceResult.fail("Audit trail integrity check failed", data=data)
    return BaseServiceResult.ok(data=data)
