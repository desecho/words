"""Serializers used by wordsapp."""

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_registration.api.serializers import DefaultRegisterUserSerializer

from wordsapp.models import PartOfSpeech, StudyGrade, StudyLanguage, Text

User = get_user_model()


class WordsRegisterSerializer(DefaultRegisterUserSerializer):
    """Register serializer with unique email validation."""

    def validate_email(self, value: str) -> str:
        """Reject duplicate email addresses."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "A user with this email is already registered."
            )
        return value


class StudyLanguageQuerySerializer(serializers.Serializer[User]):
    """Validate the study language query parameter."""

    language = serializers.ChoiceField(choices=StudyLanguage.choices)


class StudyReviewSerializer(serializers.Serializer[User]):
    """Validate a study review submission."""

    record_id = serializers.IntegerField(min_value=1)
    language = serializers.ChoiceField(choices=StudyLanguage.choices)
    grade = serializers.ChoiceField(choices=StudyGrade.choices)


class PartOfSpeechSerializer(serializers.ModelSerializer[PartOfSpeech]):
    """Serialize a part of speech option."""

    class Meta:
        """Part of speech serializer options."""

        model = PartOfSpeech
        fields = ("id", "name", "abbreviation")


class WordCreateSerializer(serializers.Serializer[User]):
    """Validate a UI word-creation request."""

    en = serializers.CharField(required=False, allow_blank=True, max_length=255)
    fr = serializers.CharField(required=False, allow_blank=True, max_length=255)
    ru = serializers.CharField(max_length=255)
    comment = serializers.CharField(required=False, allow_blank=True, max_length=255)
    part_of_speech_id = serializers.PrimaryKeyRelatedField(
        queryset=PartOfSpeech.objects.all(),
        source="part_of_speech",
    )

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        """Require at least one target-language value."""
        en = attrs.get("en", "")
        fr = attrs.get("fr", "")
        if not isinstance(en, str) or not isinstance(fr, str):
            raise serializers.ValidationError("English and French values must be strings.")
        if not en and not fr:
            raise serializers.ValidationError(
                {"non_field_errors": ["Provide at least one of English or French."]}
            )
        return attrs


class TextSerializer(serializers.ModelSerializer[Text]):
    """Serialize a user text."""

    class Meta:
        """Text serializer options."""

        model = Text
        fields = ("id", "name", "language", "content", "date_added")


class TextCreateSerializer(serializers.Serializer[User]):
    """Validate a UI text-creation request."""

    name = serializers.CharField(max_length=255)
    language = serializers.ChoiceField(choices=StudyLanguage.choices)
    content = serializers.CharField()
