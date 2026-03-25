"""Serializers used by wordsapp."""

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_registration.api.serializers import DefaultRegisterUserSerializer

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


class UserPreferencesSerializer(serializers.Serializer[User]):
    """Minimal serializer for profile settings."""

    username = serializers.CharField(read_only=True)
    email = serializers.EmailField()

    def validate_email(self, value: str) -> str:
        """Keep email addresses unique across users."""
        user = self.instance
        if (
            user is not None
            and User.objects.exclude(pk=user.pk).filter(email__iexact=value).exists()
        ):
            raise serializers.ValidationError(
                "A user with this email is already registered."
            )
        return value

    def update(self, instance: User, validated_data: dict[str, str]) -> User:
        """Persist editable profile fields."""
        instance.email = validated_data["email"]
        instance.save(update_fields=["email"])
        return instance

    def create(self, validated_data: dict[str, str]) -> User:
        """Creation is not supported by this serializer."""
        raise NotImplementedError("UserPreferencesSerializer does not create users")
