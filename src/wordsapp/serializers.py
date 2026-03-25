"""Serializers used by wordsapp."""

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_registration.api.serializers import DefaultRegisterUserSerializer

from wordsapp.models import StudyGrade, StudyLanguage

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
