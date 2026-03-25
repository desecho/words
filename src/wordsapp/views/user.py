"""User-related views for wordsapp."""

from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

User = get_user_model()


class UserCheckEmailAvailabilityView(APIView):
    """Check whether an email address is available."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        """Return True when the email address is unused."""
        email = request.data.get("email")
        if not isinstance(email, str) or not email:
            return Response({"email": ["This field is required."]}, status=400)

        is_available = not User.objects.filter(email__iexact=email).exists()
        return Response(is_available)
