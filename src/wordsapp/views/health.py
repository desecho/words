"""Health check view."""

from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    """Return a simple health payload."""

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        """Handle health check requests."""
        return Response({"status": "ok", "project": "words"})
