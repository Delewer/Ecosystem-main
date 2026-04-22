"""
Services for multimedia content in lessons
"""

import re
from typing import Optional
from urllib.parse import urlparse

from django.core.exceptions import ValidationError

from ..models import Lesson, VideoProgress


class LessonMediaService:
    """Service for handling multimedia content in lessons"""

    @staticmethod
    def get_video_embed_url(lesson: Lesson) -> str:
        """Get embed URL for video content"""
        if not lesson.video_url:
            return ""

        if lesson.video_platform == "youtube":
            video_id = LessonMediaService._extract_youtube_id(lesson.video_url)
            return f"https://www.youtube.com/embed/{video_id}" if video_id else ""

        elif lesson.video_platform == "vimeo":
            video_id = LessonMediaService._extract_vimeo_id(lesson.video_url)
            return f"https://player.vimeo.com/video/{video_id}" if video_id else ""

        return lesson.video_url

    @staticmethod
    def _extract_youtube_id(url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
        patterns = [
            r"(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})",
            r"youtube\.com\/v\/([a-zA-Z0-9_-]{11})",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    @staticmethod
    def _extract_vimeo_id(url: str) -> Optional[str]:
        """Extract Vimeo video ID from URL"""
        match = re.search(r"vimeo\.com\/(?:video\/)?(\d+)", url)
        return match.group(1) if match else None

    @staticmethod
    def track_video_progress(
        user, lesson: Lesson, watched_seconds: int, total_duration: Optional[int] = None
    ) -> bool:
        """Track video watching progress"""
        if total_duration is None:
            total_duration = lesson.video_duration_seconds

        if total_duration <= 0:
            return False

        progress, created = VideoProgress.objects.get_or_create(
            user=user, lesson=lesson
        )

        # Update watched seconds (take maximum)
        progress.watched_seconds = max(progress.watched_seconds, watched_seconds)
        progress.completion_percent = min(
            100.0, (progress.watched_seconds / total_duration) * 100
        )

        # Mark as completed if watched > 80%
        is_completed = progress.completion_percent >= 80
        if is_completed and not progress.completed_at:
            from django.utils import timezone

            progress.completed_at = timezone.now()

        progress.save()
        return is_completed

    @staticmethod
    def get_video_progress(user, lesson: Lesson) -> Optional[VideoProgress]:
        """Get video progress for user and lesson"""
        try:
            return VideoProgress.objects.get(user=user, lesson=lesson)
        except VideoProgress.DoesNotExist:
            return None

    @staticmethod
    def validate_video_url(url: str, platform: str) -> None:
        """Validate video URL based on platform"""
        if not url:
            return

        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValidationError("Invalid URL format")
        except Exception:
            raise ValidationError("Invalid URL")

        if platform == "youtube":
            if "youtube.com" not in url and "youtu.be" not in url:
                raise ValidationError("URL must be from YouTube")
        elif platform == "vimeo":
            if "vimeo.com" not in url:
                raise ValidationError("URL must be from Vimeo")

    @staticmethod
    def get_media_duration(media_type: str, url: str) -> int:
        """Get duration of media content (placeholder for future API integration)"""
        # This would integrate with YouTube/Vimeo APIs to get actual duration
        # For now, return 0 (to be set manually)
        return 0
