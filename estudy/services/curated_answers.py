from __future__ import annotations

from typing import Optional

from ..models import CommunityCuratedAnswer, CommunityReply, CommunityThread, EventLog
from .audit_logger import log_event
from .permissions import ACTION_COMMUNITY_CURATE, is_allowed
from .service_result import BaseServiceResult

ERROR_MISSING_CURATOR = "Curator is required"
ERROR_MISSING_THREAD = "Thread is required"
ERROR_MISSING_REPLY = "Reply is required"
ERROR_THREAD_MISMATCH = "Reply does not belong to thread"
ERROR_NOT_ALLOWED = "Curator role not allowed"

WARNING_ALREADY_CURATED = "already_curated"
WARNING_NOT_CURATED = "not_curated"

CURATION_ACTION_CURATE = "curate"
CURATION_ACTION_REMOVE = "remove"


def _normalize_note(note: Optional[str]) -> str:
    return (note or "").strip()


def _validate_inputs(
    *, thread: CommunityThread, reply: CommunityReply, curator
) -> BaseServiceResult:
    if curator is None:
        return BaseServiceResult.fail(ERROR_MISSING_CURATOR)
    if thread is None:
        return BaseServiceResult.fail(ERROR_MISSING_THREAD)
    if reply is None:
        return BaseServiceResult.fail(ERROR_MISSING_REPLY)
    if reply.thread_id != thread.id:
        return BaseServiceResult.fail(ERROR_THREAD_MISMATCH)
    if not is_allowed(curator, ACTION_COMMUNITY_CURATE):
        return BaseServiceResult.fail(ERROR_NOT_ALLOWED)
    return BaseServiceResult.ok()


def _log_curation_event(
    *,
    curator,
    action: str,
    thread: CommunityThread,
    reply: CommunityReply,
    curated_id: Optional[int] = None,
    note: str = "",
) -> None:
    metadata = {
        "action": action,
        "thread_id": thread.id,
        "reply_id": reply.id,
    }
    if curated_id is not None:
        metadata["curated_id"] = curated_id
    if note:
        metadata["note"] = note
    log_event(EventLog.EVENT_COMMUNITY_CURATION, user=curator, metadata=metadata)


def curate_reply(
    *,
    thread: CommunityThread,
    reply: CommunityReply,
    curator,
    note: Optional[str] = None,
) -> BaseServiceResult:
    validation = _validate_inputs(thread=thread, reply=reply, curator=curator)
    if not validation.success:
        return validation

    note_value = _normalize_note(note)
    curated, created = CommunityCuratedAnswer.objects.get_or_create(
        reply=reply,
        defaults={
            "thread": thread,
            "curated_by": curator,
            "note": note_value,
        },
    )
    if not created:
        return BaseServiceResult.ok(
            data={"curated": curated, "created": False},
            warnings=[WARNING_ALREADY_CURATED],
        )

    _log_curation_event(
        curator=curator,
        action=CURATION_ACTION_CURATE,
        thread=thread,
        reply=reply,
        curated_id=curated.id,
        note=note_value,
    )
    return BaseServiceResult.ok(data={"curated": curated, "created": True})


def remove_curated_reply(
    *,
    thread: CommunityThread,
    reply: CommunityReply,
    curator,
) -> BaseServiceResult:
    validation = _validate_inputs(thread=thread, reply=reply, curator=curator)
    if not validation.success:
        return validation

    curated = CommunityCuratedAnswer.objects.filter(thread=thread, reply=reply).first()
    if curated is None:
        return BaseServiceResult.ok(
            data={"removed": False},
            warnings=[WARNING_NOT_CURATED],
        )

    curated_id = curated.id
    curated.delete()
    _log_curation_event(
        curator=curator,
        action=CURATION_ACTION_REMOVE,
        thread=thread,
        reply=reply,
        curated_id=curated_id,
    )
    return BaseServiceResult.ok(data={"removed": True})


def get_curated_reply_ids(*, thread: CommunityThread) -> BaseServiceResult:
    if thread is None:
        return BaseServiceResult.fail(ERROR_MISSING_THREAD)
    reply_ids = set(
        CommunityCuratedAnswer.objects.filter(thread=thread).values_list(
            "reply_id", flat=True
        )
    )
    return BaseServiceResult.ok(data={"reply_ids": reply_ids})
