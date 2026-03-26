"""Text-related API views."""

from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from wordsapp.models import Text
from wordsapp.serializers import TextCreateSerializer, TextSerializer
from wordsapp.text_processing import build_text_segments


class TextListCreateView(APIView):
    """List and create texts for the authenticated user."""

    def get(self, request: Request) -> Response:
        """Return the current user's texts."""
        serializer = TextSerializer(
            Text.objects.filter(user_added=request.user).order_by("-date_added", "-pk"),
            many=True,
        )
        return Response({"texts": serializer.data})

    def post(self, request: Request) -> Response:
        """Create a text for the current user."""
        serializer = TextCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        text = Text.objects.create(user_added=request.user, **serializer.validated_data)
        return Response(
            {"text": TextSerializer(text).data},
            status=status.HTTP_201_CREATED,
        )


class TextDetailView(APIView):
    """Return or delete one of the current user's texts."""

    def get_text(self, request: Request, text_id: int) -> Text:
        """Return one text belonging to the current user."""
        return get_object_or_404(Text.objects.filter(user_added=request.user), pk=text_id)

    def get(self, request: Request, text_id: int) -> Response:
        """Return one text and its highlighted segments."""
        text = self.get_text(request, text_id)
        return Response(
            {
                "text": TextSerializer(text).data,
                "segments": build_text_segments(text.content, text.language, request.user),
            }
        )

    def delete(self, request: Request, text_id: int) -> Response:
        """Delete one text belonging to the current user."""
        text = self.get_text(request, text_id)
        text.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
