"""Models."""

from django.contrib.auth.models import AbstractUser, AnonymousUser
from django.db.models import CASCADE, CharField, DateTimeField, ForeignKey, ManyToManyField, Model, PositiveIntegerField
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
