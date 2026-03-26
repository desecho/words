"""Word-related API views."""

from __future__ import annotations

from django.db import transaction
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from wordsapp.models import PartOfSpeech, Record, Word
from wordsapp.serializers import PartOfSpeechSerializer, WordCreateSerializer
from wordsapp.views.utils import get_authenticated_user


def build_created_word_payload(word: Word, record: Record) -> dict[str, object]:
    """Return the created word payload for the UI."""
    return {
        "record_id": record.pk,
        "word": {
            "comment": word.comment,
            "en": word.en,
            "fr": word.fr,
            "id": word.pk,
            "part_of_speech": {
                "abbreviation": word.part_of_speech.abbreviation,
                "id": word.part_of_speech.pk,
                "name": word.part_of_speech.name,
            },
            "ru": word.ru,
        },
    }


class PartOfSpeechListView(APIView):
    """Return available part-of-speech options."""

    def get(self, request: Request) -> Response:
        """List part-of-speech options for the add-word form."""
        serializer = PartOfSpeechSerializer(
            PartOfSpeech.objects.order_by("name", "abbreviation", "pk"),
            many=True,
        )
        return Response({"parts_of_speech": serializer.data})


class WordCreateView(APIView):
    """Create a new word and its corresponding user record."""

    def post(self, request: Request) -> Response:
        """Create a word and a matching record for the authenticated user."""
        user = get_authenticated_user(request)
        serializer = WordCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        with transaction.atomic():
            part_of_speech = validated_data["part_of_speech"]
            word = Word.objects.create(
                user_added=user,
                en=str(validated_data.get("en", "")),
                fr=str(validated_data.get("fr", "")),
                ru=str(validated_data["ru"]),
                comment=str(validated_data.get("comment", "")),
                part_of_speech=part_of_speech,
            )
            record = Record.objects.create(user=user, word=word)

        return Response(
            build_created_word_payload(word, record),
            status=status.HTTP_201_CREATED,
        )
