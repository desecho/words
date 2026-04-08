"""URL configuration for the words project."""

from django.conf.urls import include
from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from wordsapp.views.health import HealthView
from wordsapp.views.stats import StatsSummaryView
from wordsapp.views.study import (
    StudyIncorrectWordsView,
    StudyNextCardView,
    StudyReviewView,
    StudySummaryView,
)
from wordsapp.views.text import TextDetailView, TextListCreateView
from wordsapp.views.user import UserCheckEmailAvailabilityView
from wordsapp.views.word import PartOfSpeechListView, WordDetailView, WordListCreateView

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
        "parts-of-speech/",
        PartOfSpeechListView.as_view(),
        name="part_of_speech_list",
    ),
    path("words/", WordListCreateView.as_view(), name="word_list_create"),
    path("words/<int:word_id>/", WordDetailView.as_view(), name="word_detail"),
    path("texts/", TextListCreateView.as_view(), name="text_list_create"),
    path("texts/<int:text_id>/", TextDetailView.as_view(), name="text_detail"),
    path("stats/summary/", StatsSummaryView.as_view(), name="stats_summary"),
    path("study/summary/", StudySummaryView.as_view(), name="study_summary"),
    path(
        "study/incorrect-words/",
        StudyIncorrectWordsView.as_view(),
        name="study_incorrect_words",
    ),
    path("study/next-card/", StudyNextCardView.as_view(), name="study_next_card"),
    path("study/review/", StudyReviewView.as_view(), name="study_review"),
]
