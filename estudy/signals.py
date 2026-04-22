from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse

from .models import LessonComment, LessonRating
from .services.notifications import (
    notify_comment_reply,
    notify_new_comment,
    notify_new_rating,
)


@receiver(post_save, sender=LessonComment)
def notify_on_new_comment(sender, instance, created, **kwargs):
    """Send notifications when new comments are created"""
    if created and instance.is_approved and instance.lesson.slug:
        lesson_url = reverse(
            "estudy:lesson_detail", kwargs={"slug": instance.lesson.slug}
        )

        # Notify teachers about new comment
        notify_new_comment(instance.user, instance.lesson.title, lesson_url)

        # Notify parent comment author about replies
        if instance.parent:
            notify_comment_reply(
                instance.parent.user, instance.user, instance.lesson.title, lesson_url
            )


@receiver(pre_save, sender=LessonComment)
def cache_comment_state(sender, instance, **kwargs):
    if not instance.pk:
        instance._previous_state = None
        return
    previous = (
        LessonComment.objects.filter(pk=instance.pk)
        .values("is_approved", "is_hidden")
        .first()
    )
    instance._previous_state = previous


@receiver(post_save, sender=LessonComment)
def update_comment_reputation(sender, instance, created, **kwargs):
    from .services.reputation import (
        apply_comment_moderation_reputation,
        apply_new_comment_reputation,
    )

    if created:
        apply_new_comment_reputation(instance)
        return
    previous_state = getattr(instance, "_previous_state", None)
    apply_comment_moderation_reputation(
        comment=instance,
        previous_state=previous_state,
    )


@receiver(post_save, sender=LessonRating)
def notify_on_new_rating(sender, instance, created, **kwargs):
    """Send notifications when new ratings are created"""
    if created and instance.lesson.slug:
        lesson_url = reverse(
            "estudy:lesson_detail", kwargs={"slug": instance.lesson.slug}
        )
        notify_new_rating(
            instance.user, instance.lesson.title, instance.rating, lesson_url
        )
