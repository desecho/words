"""Stats API views."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import cast

from django.db.models import Count, Q, Sum
from django.db.models.query import QuerySet
from django.utils import timezone
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from wordsapp.models import Record, StudyLanguage, StudyProgress, Text, User, Word
from wordsapp.views.study import due_progress_queryset, unseen_records_queryset
from wordsapp.views.utils import get_authenticated_user


def calculate_success_rate(successful_reviews: int, total_reviews: int) -> float:
    """Return a percentage success rate."""
    if total_reviews == 0:
        return 0.0
    return round(successful_reviews / total_reviews * 100, 1)


def eligible_progress_queryset(user: User, language: str) -> QuerySet[StudyProgress]:
    """Return progress rows backed by eligible study records."""
    prompt_filter = (
        Q(record__word__en__gt="")
        if language == StudyLanguage.ENGLISH
        else Q(record__word__fr__gt="")
    )
    return StudyProgress.objects.filter(
        user=user,
        language=language,
    ).filter(
        prompt_filter,
        record__user=user,
        record__word__ru__gt="",
        record__word__part_of_speech__abbreviation__gt="",
    )


def study_language_stats(user: User, language: str, now: datetime) -> dict[str, object]:
    """Return study stats for one language."""
    queryset = eligible_progress_queryset(user, language)
    aggregate = queryset.aggregate(
        active=Count("pk", filter=Q(ignore=False)),
        ignored=Count("pk", filter=Q(ignore=True)),
        reviewed_total=Sum("total_reviews"),
        successful_reviews=Sum("successful_reviews"),
    )
    reviewed_total = int(cast(int | None, aggregate["reviewed_total"]) or 0)
    successful_reviews = int(cast(int | None, aggregate["successful_reviews"]) or 0)
    return {
        "active": int(aggregate["active"]),
        "due": due_progress_queryset(user, language, now).count(),
        "ignored": int(aggregate["ignored"]),
        "label": StudyLanguage(language).label,
        "reviewed_total": reviewed_total,
        "success_rate": calculate_success_rate(successful_reviews, reviewed_total),
        "successful_reviews": successful_reviews,
        "unseen": unseen_records_queryset(user, language).count(),
    }


def overview_stats(user: User) -> dict[str, object]:
    """Return global overview stats."""
    aggregate = StudyProgress.objects.filter(user=user).aggregate(
        reviews_successful=Sum("successful_reviews"),
        reviews_total=Sum("total_reviews"),
    )
    reviews_total = int(cast(int | None, aggregate["reviews_total"]) or 0)
    reviews_successful = int(cast(int | None, aggregate["reviews_successful"]) or 0)
    return {
        "records_total": Record.objects.filter(user=user).count(),
        "review_success_rate": calculate_success_rate(
            reviews_successful,
            reviews_total,
        ),
        "reviews_successful": reviews_successful,
        "reviews_total": reviews_total,
        "texts_total": Text.objects.filter(user_added=user).count(),
        "words_total": Word.objects.filter(user_added=user).count(),
    }


def activity_stats(user: User, now: datetime) -> dict[str, int]:
    """Return recent activity stats."""
    cutoff = now - timedelta(days=7)
    return {
        "recent_reviews_7d": StudyProgress.objects.filter(
            user=user,
            last_reviewed_at__gte=cutoff,
        ).count(),
        "recent_texts_added_7d": Text.objects.filter(
            user_added=user,
            date_added__gte=cutoff,
        ).count(),
        "recent_words_added_7d": Word.objects.filter(
            user_added=user,
            date_added__gte=cutoff,
        ).count(),
    }


def collection_stats(user: User) -> dict[str, object]:
    """Return vocabulary collection stats."""
    queryset = Word.objects.filter(user_added=user)
    coverage = queryset.aggregate(
        with_both=Count("pk", filter=Q(en__gt="", fr__gt="")),
        with_english=Count("pk", filter=Q(en__gt="")),
        with_french=Count("pk", filter=Q(fr__gt="")),
    )
    parts_of_speech_rows = (
        queryset.values("part_of_speech__abbreviation", "part_of_speech__name")
        .annotate(count=Count("pk"))
        .order_by(
            "-count",
            "part_of_speech__name",
            "part_of_speech__abbreviation",
        )
    )
    parts_of_speech = []
    for row in parts_of_speech_rows:
        abbreviation = str(row["part_of_speech__abbreviation"])
        name = str(row["part_of_speech__name"])
        label = f"{name} ({abbreviation})" if abbreviation else name
        parts_of_speech.append({"count": int(row["count"]), "label": label})
    return {
        "language_coverage": {
            "with_both": int(coverage["with_both"]),
            "with_english": int(coverage["with_english"]),
            "with_french": int(coverage["with_french"]),
        },
        "parts_of_speech": parts_of_speech,
    }


class StatsSummaryView(APIView):
    """Return a dashboard summary for the current user."""

    def get(self, request: Request) -> Response:
        """Return dashboard stats for the current user."""
        user = get_authenticated_user(request)
        now = timezone.now()
        return Response(
            {
                "activity": activity_stats(user, now),
                "collection": collection_stats(user),
                "overview": overview_stats(user),
                "study": {
                    language: study_language_stats(user, language, now)
                    for language in StudyLanguage.values
                },
            }
        )
