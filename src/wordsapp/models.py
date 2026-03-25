"""Models."""

from django.contrib.auth.models import AbstractUser, AnonymousUser
from django.db.models import (
    CASCADE,
    BooleanField,
    CharField,
    DateTimeField,
    FloatField,
    ForeignKey,
    ManyToManyField,
    Model,
    PositiveIntegerField,
    TextChoices,
    UniqueConstraint,
)
from django.http import HttpRequest


class UserBase:
    """User base class."""

    pass


class User(AbstractUser, UserBase):
    """User class."""

    class Meta:
        """Meta options for User model."""

        app_label = "wordsapp"

    def __str__(self) -> str:
        """Return string representation."""
        if self.username and not self.username.isnumeric():
            return self.username
        return self.get_full_name()


class UserAnonymous(AnonymousUser, UserBase):
    """Anonymous user class."""

    # Not sure if it is needed.
    def __init__(self, request: HttpRequest):
        """Init."""
        super().__init__()


class PartOfSpeech(Model):
    """Part of speech."""

    name = CharField(max_length=255)
    abbreviation = CharField(max_length=255)

    def __str__(self) -> str:
        """Return string representation."""
        return self.name


class Tag(Model):
    """Tag."""

    name = CharField(max_length=255)

    def __str__(self) -> str:
        """Return string representation."""
        return self.name


class Word(Model):
    """Word."""

    user_added = ForeignKey(User, CASCADE, related_name="words")
    en = CharField(max_length=255)
    ru = CharField(max_length=255, blank=True)
    fr = CharField(max_length=255, blank=True)
    part_of_speech = ForeignKey(PartOfSpeech, CASCADE, related_name="words")
    tags = ManyToManyField(Tag, related_name="words", blank=True)
    date_added = DateTimeField(auto_now_add=True)
    frequency = PositiveIntegerField(unique=True, null=True, blank=True)
    comment = CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        """Return string representation."""
        return self.en


class Record(Model):
    """Word record."""

    word = ForeignKey(Word, CASCADE, related_name="records")
    user = ForeignKey(User, CASCADE, related_name="records")
    date_added = DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.user} - {self.word}"


class StudyLanguage(TextChoices):
    """Supported study languages."""

    ENGLISH = "en", "English"
    FRENCH = "fr", "French"


class StudyGrade(TextChoices):
    """Supported self-assessment grades."""

    INCORRECT = "incorrect", "Incorrect"
    CORRECT = "correct", "Correct"
    IGNORE = "ignore", "Ignore"


class StudyProgress(Model):
    """Per-user spaced repetition state for a record and study language."""

    user = ForeignKey(User, CASCADE, related_name="study_progresses")
    record = ForeignKey(Record, CASCADE, related_name="study_progresses")
    language = CharField(max_length=2, choices=StudyLanguage.choices)
    ignore = BooleanField(default=False)
    repetition = PositiveIntegerField(default=0)
    interval_days = PositiveIntegerField(default=0)
    easiness_factor = FloatField(default=2.5)
    due_at = DateTimeField()
    last_reviewed_at = DateTimeField(null=True, blank=True)
    last_quality = PositiveIntegerField(null=True, blank=True)
    last_grade = CharField(max_length=16, choices=StudyGrade.choices, blank=True)
    total_reviews = PositiveIntegerField(default=0)
    successful_reviews = PositiveIntegerField(default=0)

    class Meta:
        """Meta options for StudyProgress."""

        constraints = [
            UniqueConstraint(
                fields=("user", "record", "language"),
                name="wordsapp_studyprogress_user_record_language_uniq",
            )
        ]

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.user} - {self.record} - {self.language}"
