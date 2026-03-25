"""URL configuration for the words project."""

from django.conf.urls import include
from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from wordsapp.views.health import HealthView
from wordsapp.views.user import UserCheckEmailAvailabilityView, UserPreferencesView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", HealthView.as_view(), name="health"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("user/", include("rest_registration.api.urls")),
    path(
        "user/check-email-availability/",
        UserCheckEmailAvailabilityView.as_view(),
        name="check_email_availability",
    ),
    path(
        "user/preferences/",
        UserPreferencesView.as_view(),
        name="user_preferences",
    ),
]
