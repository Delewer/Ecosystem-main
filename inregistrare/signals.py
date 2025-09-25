from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from estudy.models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Создать профиль только если его нет
        UserProfile.objects.get_or_create(user=instance)
    else:
        if hasattr(instance, 'userprofile'):
            instance.userprofile.save()
