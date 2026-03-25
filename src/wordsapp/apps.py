"""App configuration for wordsapp."""

from django.apps import AppConfig


class WordsAppConfig(AppConfig):
    """Configuration for the words application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "wordsapp"
