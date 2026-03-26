"""Word-related API views."""

from __future__ import annotations

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from wordsapp.models import PartOfSpeech, Record, Word
from wordsapp.serializers import (
    PartOfSpeechSerializer,
    WordCreateSerializer,
    WordSerializer,
    WordUpdateSerializer,
)
from wordsapp.views.utils import get_authenticated_user


def build_created_word_payload(word: Word, record: Record) -> dict[str, object]:
    """Return the created word payload for the UI."""
    return {
        "record_id": record.pk,
        "word": WordSerializer(word).data,
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


class WordListCreateView(APIView):
    """List and create words for the authenticated user."""

    def get(self, request: Request) -> Response:
        """Return the current user's words, optionally filtered by search."""
        user = get_authenticated_user(request)
        search = request.query_params.get("search", "").strip()
        queryset = Word.objects.filter(user_added=user).select_related("part_of_speech")

        if search:
            queryset = queryset.filter(
                Q(ru__icontains=search)
                | Q(en__icontains=search)
                | Q(fr__icontains=search)
            )

        serializer = WordSerializer(
            queryset.order_by("-date_added", "-pk"),
            many=True,
        )
        return Response({"words": serializer.data})

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


class WordDetailView(APIView):
    """Update or delete one of the current user's words."""

    def get_word(self, request: Request, word_id: int) -> Word:
        """Return one word belonging to the current user."""
        user = get_authenticated_user(request)
        return get_object_or_404(
            Word.objects.filter(user_added=user).select_related("part_of_speech"),
            pk=word_id,
        )

    def patch(self, request: Request, word_id: int) -> Response:
        """Update one word belonging to the current user."""
        word = self.get_word(request, word_id)
        serializer = WordUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        word.ru = str(validated_data["ru"])
        word.en = str(validated_data.get("en", ""))
        word.fr = str(validated_data.get("fr", ""))
        word.comment = str(validated_data.get("comment", ""))
        word.part_of_speech = validated_data["part_of_speech"]
        word.save(
            update_fields=["ru", "en", "fr", "comment", "part_of_speech"]
        )
        word.refresh_from_db()
        return Response({"word": WordSerializer(word).data})

    def delete(self, request: Request, word_id: int) -> Response:
        """Delete one word belonging to the current user."""
        word = self.get_word(request, word_id)
        word.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
