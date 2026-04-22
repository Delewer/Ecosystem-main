from django.apps import AppConfig


class InregistrareConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "inregistrare"

    def ready(self):
        import inregistrare.signals  # Убедитесь, что путь корректный  # noqa: F401
