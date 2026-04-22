from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(blank=True, null=True)
    email = models.EmailField(max_length=254)
    name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    age = models.PositiveSmallIntegerField(
        "Vârstă",
        blank=True,
        null=True,
        validators=[MinValueValidator(6), MaxValueValidator(100)],
    )
    accepted_terms = models.BooleanField("Termeni acceptați", default=False)
    accepted_terms_at = models.DateTimeField(
        "Data acceptării termenilor", blank=True, null=True
    )
    accepted_terms_version = models.CharField(
        "Versiunea termenilor", max_length=20, blank=True, default="v1"
    )

    def __str__(self):
        return self.user.username
