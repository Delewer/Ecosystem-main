import csv
import io
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import EventLog, Lesson, LessonAnalytics, Subject
from .services.analytics_export import (
    EXPORT_KIND_EVENT_LOG,
    EXPORT_KIND_LESSON_ANALYTICS,
    LIMIT_CLAMP_WARNING,
    MAX_EXPORT_LIMIT,
    build_bigquery_payload,
    export_analytics_to_csv,
)

USER_PASSWORD = "pass1234"
EXPECTED_ROW_COUNT = 1
DATE_RANGE_OFFSET_DAYS = 1
LIMIT_OVERFLOW = 1
HEADER_ROW_INDEX = 0
FIRST_DATA_ROW_INDEX = 1
EVENT_TYPE_COLUMN_INDEX = 2

ANALYTICS_VIEWS = 10
ANALYTICS_UNIQUE_VIEWS = 7
ANALYTICS_COMPLETIONS = 5
ANALYTICS_AVG_TIME = 120
ANALYTICS_MEDIAN_TIME = 100
ANALYTICS_AVG_SCORE = 80
ANALYTICS_COMPLETION_RATE = 70
ANALYTICS_COMMENTS_COUNT = 1
ANALYTICS_RATINGS_COUNT = 1
ANALYTICS_AVG_RATING = 4
ANALYTICS_ERROR_COUNT = 0
ANALYTICS_LOAD_TIME = 1000

EVENT_LOG_COLUMNS = [
    "id",
    "user_id",
    "event_type",
    "created_at",
    "metadata",
]

LESSON_ANALYTICS_COLUMNS = [
    "id",
    "lesson_id",
    "date",
    "views",
    "unique_views",
    "completions",
    "avg_time_spent",
    "median_time_spent",
    "avg_score",
    "completion_rate",
    "comments_count",
    "ratings_count",
    "avg_rating",
    "error_count",
    "load_time_avg",
]


class AnalyticsExportTests(TestCase):
    def _create_lesson(self) -> Lesson:
        subject = Subject.objects.create(name="Data")
        return Lesson.objects.create(
            subject=subject,
            title="Lesson One",
            content="Sample content",
            date=timezone.localdate(),
        )

    def test_export_event_log_csv(self):
        user = User.objects.create_user(username="u1", password=USER_PASSWORD)
        EventLog.objects.create(user=user, event_type=EventLog.EVENT_LOGIN)

        result = export_analytics_to_csv(kind=EXPORT_KIND_EVENT_LOG)

        self.assertTrue(result.success)
        self.assertEqual(result.data["row_count"], EXPECTED_ROW_COUNT)
        self.assertEqual(result.data["columns"], EVENT_LOG_COLUMNS)

        reader = csv.reader(io.StringIO(result.data["csv"]))
        rows = list(reader)
        self.assertEqual(rows[HEADER_ROW_INDEX], EVENT_LOG_COLUMNS)
        self.assertEqual(
            rows[FIRST_DATA_ROW_INDEX][EVENT_TYPE_COLUMN_INDEX],
            EventLog.EVENT_LOGIN,
        )

    def test_export_lesson_analytics_bigquery(self):
        lesson = self._create_lesson()
        LessonAnalytics.objects.create(
            lesson=lesson,
            date=timezone.localdate(),
            views=ANALYTICS_VIEWS,
            unique_views=ANALYTICS_UNIQUE_VIEWS,
            completions=ANALYTICS_COMPLETIONS,
            avg_time_spent=ANALYTICS_AVG_TIME,
            median_time_spent=ANALYTICS_MEDIAN_TIME,
            avg_score=ANALYTICS_AVG_SCORE,
            completion_rate=ANALYTICS_COMPLETION_RATE,
            comments_count=ANALYTICS_COMMENTS_COUNT,
            ratings_count=ANALYTICS_RATINGS_COUNT,
            avg_rating=ANALYTICS_AVG_RATING,
            error_count=ANALYTICS_ERROR_COUNT,
            load_time_avg=ANALYTICS_LOAD_TIME,
        )

        result = build_bigquery_payload(kind=EXPORT_KIND_LESSON_ANALYTICS)

        self.assertTrue(result.success)
        self.assertEqual(result.data["row_count"], EXPECTED_ROW_COUNT)
        schema_names = [field["name"] for field in result.data["schema"]]
        self.assertEqual(schema_names, LESSON_ANALYTICS_COLUMNS)
        row = result.data["rows"][0]
        self.assertEqual(row["views"], ANALYTICS_VIEWS)
        self.assertEqual(row["lesson_id"], lesson.id)

    def test_export_invalid_kind(self):
        result = export_analytics_to_csv(kind="unknown")

        self.assertFalse(result.success)

    def test_export_invalid_date(self):
        result = export_analytics_to_csv(
            kind=EXPORT_KIND_EVENT_LOG,
            start="bad-date",
        )

        self.assertFalse(result.success)

    def test_export_date_range_validation(self):
        start_date = timezone.localdate()
        end_date = start_date - timedelta(days=DATE_RANGE_OFFSET_DAYS)

        result = export_analytics_to_csv(
            kind=EXPORT_KIND_EVENT_LOG,
            start=start_date,
            end=end_date,
        )

        self.assertFalse(result.success)

    def test_export_limit_clamped(self):
        user = User.objects.create_user(username="u2", password=USER_PASSWORD)
        EventLog.objects.create(user=user, event_type=EventLog.EVENT_LOGIN)

        result = export_analytics_to_csv(
            kind=EXPORT_KIND_EVENT_LOG,
            limit=MAX_EXPORT_LIMIT + LIMIT_OVERFLOW,
        )

        self.assertTrue(result.success)
        self.assertIn(LIMIT_CLAMP_WARNING, result.warnings)
