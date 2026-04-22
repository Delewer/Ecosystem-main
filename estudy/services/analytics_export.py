from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable

from ..models import EventLog, LessonAnalytics, LessonProgress, TestAttempt
from .service_result import BaseServiceResult

FIELD_TYPE_STRING = "string"
FIELD_TYPE_INT = "int"
FIELD_TYPE_FLOAT = "float"
FIELD_TYPE_BOOL = "bool"
FIELD_TYPE_DATE = "date"
FIELD_TYPE_TIMESTAMP = "timestamp"
FIELD_TYPE_JSON = "json"

BIGQUERY_TYPE_STRING = "STRING"
BIGQUERY_TYPE_INTEGER = "INTEGER"
BIGQUERY_TYPE_FLOAT = "FLOAT"
BIGQUERY_TYPE_BOOLEAN = "BOOLEAN"
BIGQUERY_TYPE_DATE = "DATE"
BIGQUERY_TYPE_TIMESTAMP = "TIMESTAMP"
BIGQUERY_MODE_NULLABLE = "NULLABLE"

BIGQUERY_TYPE_MAP = {
    FIELD_TYPE_STRING: BIGQUERY_TYPE_STRING,
    FIELD_TYPE_INT: BIGQUERY_TYPE_INTEGER,
    FIELD_TYPE_FLOAT: BIGQUERY_TYPE_FLOAT,
    FIELD_TYPE_BOOL: BIGQUERY_TYPE_BOOLEAN,
    FIELD_TYPE_DATE: BIGQUERY_TYPE_DATE,
    FIELD_TYPE_TIMESTAMP: BIGQUERY_TYPE_TIMESTAMP,
    FIELD_TYPE_JSON: BIGQUERY_TYPE_STRING,
}

DATE_FIELD_TYPE_DATE = "date"
DATE_FIELD_TYPE_DATETIME = "datetime"

DEFAULT_EXPORT_LIMIT = 10000
MAX_EXPORT_LIMIT = 50000
MIN_EXPORT_LIMIT = 1

LIMIT_CLAMP_WARNING = "limit_clamped"
NO_ROWS_WARNING = "no_rows"

EXPORT_ERROR_INVALID_KIND = "Unsupported export kind"
EXPORT_ERROR_INVALID_LIMIT = "Limit must be a positive integer"
EXPORT_ERROR_DATE_ORDER = "Start date must be before end date"
EXPORT_ERROR_INVALID_DATE_TEMPLATE = "Invalid {label} date"

EXPORT_KIND_EVENT_LOG = "event_log"
EXPORT_KIND_LESSON_ANALYTICS = "lesson_analytics"
EXPORT_KIND_LESSON_PROGRESS = "lesson_progress"
EXPORT_KIND_TEST_ATTEMPT = "test_attempt"

EXPORT_FORMAT_CSV = "csv"
EXPORT_FORMAT_BIGQUERY = "bigquery"

SUPPORTED_EXPORT_FORMATS = frozenset({EXPORT_FORMAT_CSV, EXPORT_FORMAT_BIGQUERY})

CSV_NEWLINE = ""
CSV_LINE_TERMINATOR = "\n"
NDJSON_LINE_TERMINATOR = "\n"
JSON_SEPARATORS = (",", ":")

DEFAULT_EXPORT_FILENAME = "analytics_export"
DEFAULT_EXPORT_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
DEFAULT_EXPORT_EXTENSION_CSV = ".csv"
DEFAULT_EXPORT_EXTENSION_BIGQUERY = ".ndjson"
DEFAULT_SCHEMA_SUFFIX = ".schema.json"

ORDER_BY_CREATED = ("created_at", "id")
ORDER_BY_UPDATED = ("updated_at", "id")
ORDER_BY_DATE = ("date", "id")


@dataclass(frozen=True)
class ExportField:
    name: str
    field_type: str
    source: str | None = None


@dataclass(frozen=True)
class ExportSpec:
    kind: str
    model: type
    fields: tuple[ExportField, ...]
    date_field: str
    date_field_type: str
    order_by: tuple[str, ...]


EVENT_LOG_FIELDS = (
    ExportField("id", FIELD_TYPE_INT, "id"),
    ExportField("user_id", FIELD_TYPE_INT, "user_id"),
    ExportField("event_type", FIELD_TYPE_STRING, "event_type"),
    ExportField("created_at", FIELD_TYPE_TIMESTAMP, "created_at"),
    ExportField("metadata", FIELD_TYPE_JSON, "metadata"),
)

LESSON_ANALYTICS_FIELDS = (
    ExportField("id", FIELD_TYPE_INT, "id"),
    ExportField("lesson_id", FIELD_TYPE_INT, "lesson_id"),
    ExportField("date", FIELD_TYPE_DATE, "date"),
    ExportField("views", FIELD_TYPE_INT, "views"),
    ExportField("unique_views", FIELD_TYPE_INT, "unique_views"),
    ExportField("completions", FIELD_TYPE_INT, "completions"),
    ExportField("avg_time_spent", FIELD_TYPE_INT, "avg_time_spent"),
    ExportField("median_time_spent", FIELD_TYPE_INT, "median_time_spent"),
    ExportField("avg_score", FIELD_TYPE_FLOAT, "avg_score"),
    ExportField("completion_rate", FIELD_TYPE_FLOAT, "completion_rate"),
    ExportField("comments_count", FIELD_TYPE_INT, "comments_count"),
    ExportField("ratings_count", FIELD_TYPE_INT, "ratings_count"),
    ExportField("avg_rating", FIELD_TYPE_FLOAT, "avg_rating"),
    ExportField("error_count", FIELD_TYPE_INT, "error_count"),
    ExportField("load_time_avg", FIELD_TYPE_INT, "load_time_avg"),
)

LESSON_PROGRESS_FIELDS = (
    ExportField("id", FIELD_TYPE_INT, "id"),
    ExportField("user_id", FIELD_TYPE_INT, "user_id"),
    ExportField("lesson_id", FIELD_TYPE_INT, "lesson_id"),
    ExportField("completed", FIELD_TYPE_BOOL, "completed"),
    ExportField("updated_at", FIELD_TYPE_TIMESTAMP, "updated_at"),
    ExportField("completed_at", FIELD_TYPE_TIMESTAMP, "completed_at"),
    ExportField("points_earned", FIELD_TYPE_INT, "points_earned"),
    ExportField(
        "fastest_completion_seconds",
        FIELD_TYPE_INT,
        "fastest_completion_seconds",
    ),
)

TEST_ATTEMPT_FIELDS = (
    ExportField("id", FIELD_TYPE_INT, "id"),
    ExportField("user_id", FIELD_TYPE_INT, "user_id"),
    ExportField("test_id", FIELD_TYPE_INT, "test_id"),
    ExportField("selected_answer", FIELD_TYPE_STRING, "selected_answer"),
    ExportField("is_correct", FIELD_TYPE_BOOL, "is_correct"),
    ExportField("created_at", FIELD_TYPE_TIMESTAMP, "created_at"),
    ExportField("time_taken_ms", FIELD_TYPE_INT, "time_taken_ms"),
    ExportField("awarded_points", FIELD_TYPE_INT, "awarded_points"),
    ExportField("earned_bonus", FIELD_TYPE_BOOL, "earned_bonus"),
    ExportField("feedback", FIELD_TYPE_STRING, "feedback"),
)


EXPORT_SPECS = {
    EXPORT_KIND_EVENT_LOG: ExportSpec(
        kind=EXPORT_KIND_EVENT_LOG,
        model=EventLog,
        fields=EVENT_LOG_FIELDS,
        date_field="created_at",
        date_field_type=DATE_FIELD_TYPE_DATETIME,
        order_by=ORDER_BY_CREATED,
    ),
    EXPORT_KIND_LESSON_ANALYTICS: ExportSpec(
        kind=EXPORT_KIND_LESSON_ANALYTICS,
        model=LessonAnalytics,
        fields=LESSON_ANALYTICS_FIELDS,
        date_field="date",
        date_field_type=DATE_FIELD_TYPE_DATE,
        order_by=ORDER_BY_DATE,
    ),
    EXPORT_KIND_LESSON_PROGRESS: ExportSpec(
        kind=EXPORT_KIND_LESSON_PROGRESS,
        model=LessonProgress,
        fields=LESSON_PROGRESS_FIELDS,
        date_field="updated_at",
        date_field_type=DATE_FIELD_TYPE_DATETIME,
        order_by=ORDER_BY_UPDATED,
    ),
    EXPORT_KIND_TEST_ATTEMPT: ExportSpec(
        kind=EXPORT_KIND_TEST_ATTEMPT,
        model=TestAttempt,
        fields=TEST_ATTEMPT_FIELDS,
        date_field="created_at",
        date_field_type=DATE_FIELD_TYPE_DATETIME,
        order_by=ORDER_BY_CREATED,
    ),
}

SUPPORTED_EXPORT_KINDS = frozenset(EXPORT_SPECS.keys())


def _parse_date_value(value: Any, label: str) -> tuple[date | None, str | None]:
    if value is None:
        return None, None
    if isinstance(value, str) and not value.strip():
        return None, None
    if isinstance(value, datetime):
        return value.date(), None
    if isinstance(value, date):
        return value, None
    if isinstance(value, str):
        try:
            if "T" in value:
                return datetime.fromisoformat(value).date(), None
            return date.fromisoformat(value), None
        except ValueError:
            return None, EXPORT_ERROR_INVALID_DATE_TEMPLATE.format(label=label)
    return None, EXPORT_ERROR_INVALID_DATE_TEMPLATE.format(label=label)


def _normalize_limit(value: Any) -> tuple[int, list[str]]:
    if value is None:
        return DEFAULT_EXPORT_LIMIT, []
    try:
        limit = int(value)
    except (TypeError, ValueError):
        raise ValueError(EXPORT_ERROR_INVALID_LIMIT)
    if limit < MIN_EXPORT_LIMIT:
        raise ValueError(EXPORT_ERROR_INVALID_LIMIT)
    warnings = []
    if limit > MAX_EXPORT_LIMIT:
        limit = MAX_EXPORT_LIMIT
        warnings.append(LIMIT_CLAMP_WARNING)
    return limit, warnings


def _build_sources(spec: ExportSpec) -> tuple[str, ...]:
    sources = []
    for field in spec.fields:
        source = field.source or field.name
        if source not in sources:
            sources.append(source)
    return tuple(sources)


def _build_queryset(
    spec: ExportSpec,
    start_date: date | None,
    end_date: date | None,
    limit: int,
):
    queryset = spec.model.objects.all()
    if start_date:
        if spec.date_field_type == DATE_FIELD_TYPE_DATETIME:
            queryset = queryset.filter(**{f"{spec.date_field}__date__gte": start_date})
        else:
            queryset = queryset.filter(**{f"{spec.date_field}__gte": start_date})
    if end_date:
        if spec.date_field_type == DATE_FIELD_TYPE_DATETIME:
            queryset = queryset.filter(**{f"{spec.date_field}__date__lte": end_date})
        else:
            queryset = queryset.filter(**{f"{spec.date_field}__lte": end_date})
    queryset = queryset.order_by(*spec.order_by)
    sources = _build_sources(spec)
    if sources:
        queryset = queryset.values(*sources)
    return list(queryset[:limit])


def _extract_value(row: dict[str, Any], field: ExportField) -> Any:
    key = field.source or field.name
    return row.get(key)


def _format_value(value: Any, field_type: str, *, for_csv: bool) -> Any:
    if value is None:
        return "" if for_csv else None
    if field_type == FIELD_TYPE_DATE:
        if isinstance(value, datetime):
            return value.date().isoformat()
        if isinstance(value, date):
            return value.isoformat()
        return str(value)
    if field_type == FIELD_TYPE_TIMESTAMP:
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)
    if field_type == FIELD_TYPE_JSON:
        return json.dumps(value, ensure_ascii=True, separators=JSON_SEPARATORS)
    return value


def _build_csv(
    columns: Iterable[str],
    rows: Iterable[dict[str, Any]],
    fields: Iterable[ExportField],
) -> str:
    buffer = io.StringIO(newline=CSV_NEWLINE)
    writer = csv.writer(buffer, lineterminator=CSV_LINE_TERMINATOR)
    writer.writerow(list(columns))
    for row in rows:
        writer.writerow(
            [
                _format_value(
                    _extract_value(row, field),
                    field.field_type,
                    for_csv=True,
                )
                for field in fields
            ]
        )
    return buffer.getvalue()


def _build_bigquery_schema(fields: Iterable[ExportField]) -> list[dict[str, str]]:
    schema = []
    for field in fields:
        schema.append(
            {
                "name": field.name,
                "type": BIGQUERY_TYPE_MAP.get(
                    field.field_type,
                    BIGQUERY_TYPE_STRING,
                ),
                "mode": BIGQUERY_MODE_NULLABLE,
            }
        )
    return schema


def _build_bigquery_rows(
    rows: Iterable[dict[str, Any]],
    fields: Iterable[ExportField],
) -> list[dict[str, Any]]:
    payload = []
    for row in rows:
        payload.append(
            {
                field.name: _format_value(
                    _extract_value(row, field),
                    field.field_type,
                    for_csv=False,
                )
                for field in fields
            }
        )
    return payload


def _prepare_export(
    *,
    kind: str,
    start: Any | None,
    end: Any | None,
    limit: int | None,
) -> BaseServiceResult:
    spec = EXPORT_SPECS.get(kind)
    if spec is None:
        return BaseServiceResult.fail(EXPORT_ERROR_INVALID_KIND)

    start_date, start_error = _parse_date_value(start, "start")
    if start_error:
        return BaseServiceResult.fail(start_error)
    end_date, end_error = _parse_date_value(end, "end")
    if end_error:
        return BaseServiceResult.fail(end_error)
    if start_date and end_date and start_date > end_date:
        return BaseServiceResult.fail(EXPORT_ERROR_DATE_ORDER)

    try:
        limit_value, warnings = _normalize_limit(limit)
    except ValueError as exc:
        return BaseServiceResult.fail(str(exc))

    rows = _build_queryset(spec, start_date, end_date, limit_value)
    if not rows:
        warnings.append(NO_ROWS_WARNING)

    return BaseServiceResult.ok(
        data={"spec": spec, "rows": rows},
        warnings=warnings,
    )


def export_analytics_to_csv(
    *,
    kind: str,
    start: Any | None = None,
    end: Any | None = None,
    limit: int | None = DEFAULT_EXPORT_LIMIT,
) -> BaseServiceResult:
    prepared = _prepare_export(
        kind=kind,
        start=start,
        end=end,
        limit=limit,
    )
    if not prepared.success:
        return prepared

    spec = prepared.data["spec"]
    rows = prepared.data["rows"]
    columns = [field.name for field in spec.fields]
    csv_text = _build_csv(columns, rows, spec.fields)
    return BaseServiceResult.ok(
        data={
            "csv": csv_text,
            "row_count": len(rows),
            "columns": columns,
            "kind": spec.kind,
        },
        warnings=prepared.warnings,
    )


def build_bigquery_payload(
    *,
    kind: str,
    start: Any | None = None,
    end: Any | None = None,
    limit: int | None = DEFAULT_EXPORT_LIMIT,
) -> BaseServiceResult:
    prepared = _prepare_export(
        kind=kind,
        start=start,
        end=end,
        limit=limit,
    )
    if not prepared.success:
        return prepared

    spec = prepared.data["spec"]
    rows = prepared.data["rows"]
    payload_rows = _build_bigquery_rows(rows, spec.fields)
    schema = _build_bigquery_schema(spec.fields)
    return BaseServiceResult.ok(
        data={
            "rows": payload_rows,
            "schema": schema,
            "row_count": len(payload_rows),
            "kind": spec.kind,
        },
        warnings=prepared.warnings,
    )


def serialize_bigquery_rows(rows: Iterable[dict[str, Any]]) -> str:
    return NDJSON_LINE_TERMINATOR.join(
        json.dumps(row, ensure_ascii=True, separators=JSON_SEPARATORS) for row in rows
    )
