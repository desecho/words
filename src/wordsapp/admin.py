"""Admin configuration for wordsapp."""

from django.contrib.admin import ModelAdmin, register

from wordsapp.models import PartOfSpeech, Record, StudyProgress, Tag, Word


@register(PartOfSpeech)
class PartOfSpeechAdmin(ModelAdmin):
    """Admin configuration for parts of speech."""

    list_display = ("name", "abbreviation")
    search_fields = ("name", "abbreviation")


@register(Tag)
class TagAdmin(ModelAdmin):
    """Admin configuration for tags."""

    list_display = ("name",)
    search_fields = ("name",)


@register(Word)
class WordAdmin(ModelAdmin):
    """Admin configuration for words."""

    filter_horizontal = ("tags",)
    list_display = (
        "en",
        "ru",
        "fr",
        "part_of_speech",
        "frequency",
        "user_added",
        "date_added",
    )
    list_filter = ("part_of_speech", "tags")
    list_select_related = ("part_of_speech", "user_added")
    search_fields = (
        "en",
        "ru",
        "fr",
        "tags__name",
        "user_added__username",
        "user_added__first_name",
        "user_added__last_name",
    )


@register(Record)
class RecordAdmin(ModelAdmin):
    """Admin configuration for records."""

    list_display = ("word", "user", "date_added")
    list_filter = ("date_added",)
    list_select_related = ("word", "user")
    search_fields = (
        "word__en",
        "word__ru",
        "word__fr",
        "user__username",
        "user__first_name",
        "user__last_name",
    )


@register(StudyProgress)
class StudyProgressAdmin(ModelAdmin):
    """Admin configuration for study progress."""

    list_display = (
        "record",
        "user",
        "language",
        "repetition",
        "interval_days",
        "easiness_factor",
        "due_at",
        "last_grade",
    )
    list_filter = ("language", "last_grade")
    list_select_related = ("record__word", "user")
    search_fields = (
        "record__word__en",
        "record__word__fr",
        "record__word__ru",
        "record__word__part_of_speech__abbreviation",
        "user__username",
        "user__first_name",
        "user__last_name",
    )
