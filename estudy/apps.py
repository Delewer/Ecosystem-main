from django.apps import AppConfig


class EstudyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "estudy"

    def ready(self):
        import estudy.signals  # noqa
