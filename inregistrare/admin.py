from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "email",
        "age",
        "accepted_terms",
        "accepted_terms_at",
        "accepted_terms_version",
    )
    list_filter = ("accepted_terms", "accepted_terms_version")
    search_fields = ("user__username", "email", "name", "phone_number")
