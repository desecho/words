"""View helpers."""

from rest_framework.exceptions import NotAuthenticated
from rest_framework.request import Request

from wordsapp.models import User


def get_authenticated_user(request: Request) -> User:
    """Return the authenticated user attached to the request."""
    user = request.user
    if isinstance(user, User):
        return user
    raise NotAuthenticated()
