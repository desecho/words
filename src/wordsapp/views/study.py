"""Study-related views and helpers."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Final, cast

from django.db import transaction
from django.db.models import Exists, F, OuterRef, Q, QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from wordsapp.models import Record, StudyGrade, StudyLanguage, StudyProgress, User
from wordsapp.serializers import StudyLanguageQuerySerializer, StudyReviewSerializer

MIN_EASINESS_FACTOR: Final[float] = 1.3
INITIAL_EASINESS_FACTOR: Final[float] = 2.5
STUDY_QUALITY_BY_GRADE: Final[dict[str, int]] = {
    StudyGrade.INCORRECT: 2,
    StudyGrade.CORRECT: 5,
}


def eligible_records_queryset(user: User, language: str) -> QuerySet[Record]:
    """Return records eligible for the requested study language."""
    prompt_filter = (
        Q(word__en__gt="")
        if language == StudyLanguage.ENGLISH
        else Q(word__fr__gt="")
    )
    return (
        Record.objects.filter(user=user)
        .select_related("word__part_of_speech")
        .filter(
            prompt_filter,
            word__ru__gt="",
            word__part_of_speech__abbreviation__gt="",
        )
    )


def unseen_records_queryset(user: User, language: str) -> QuerySet[Record]:
    """Return eligible records with no study progress for the requested language."""
    existing_progress = StudyProgress.objects.filter(
        user=user,
        record_id=OuterRef("pk"),
        language=language,
    )
    return eligible_records_queryset(user, language).annotate(
        has_progress=Exists(existing_progress)
    ).filter(has_progress=False)


def due_progress_queryset(
    user: User,
    language: str,
    now: datetime,
) -> QuerySet[StudyProgress]:
    """Return due study progress entries for the requested language."""
    prompt_filter = (
        Q(record__word__en__gt="")
        if language == StudyLanguage.ENGLISH
        else Q(record__word__fr__gt="")
    )
    return (
        StudyProgress.objects.filter(
            user=user,
            language=language,
            due_at__lte=now,
        )
        .select_related("record__word__part_of_speech")
        .filter(
            prompt_filter,
            record__user=user,
            record__word__ru__gt="",
            record__word__part_of_speech__abbreviation__gt="",
        )
    )


def build_card_payload(record: Record, language: str) -> dict[str, object]:
    """Build the flashcard payload for the frontend."""
    prompt_word = record.word.en if language == StudyLanguage.ENGLISH else record.word.fr
    part_of_speech_abbreviation = record.word.part_of_speech.abbreviation
    comment = record.word.comment.strip()
    prompt = f"{prompt_word} ({part_of_speech_abbreviation})"
    if comment:
        prompt = f"{prompt} - {comment}"
    return {
        "answer": record.word.ru,
        "comment": comment,
        "language": language,
        "part_of_speech_abbreviation": part_of_speech_abbreviation,
        "prompt": prompt,
        "record_id": record.pk,
    }


def get_next_card(user: User, language: str, now: datetime) -> dict[str, object] | None:
    """Return the next due or unseen card for a language."""
    due_progress = (
        due_progress_queryset(user, language, now)
        .order_by(
            "due_at",
            F("record__word__frequency").asc(nulls_last=True),
            "record__date_added",
            "pk",
        )
        .first()
    )
    if due_progress is not None:
        return build_card_payload(due_progress.record, language)

    unseen_record = (
        unseen_records_queryset(user, language)
        .order_by(
            F("word__frequency").asc(nulls_last=True),
            "date_added",
            "pk",
        )
        .first()
    )
    if unseen_record is None:
        return None
    return build_card_payload(unseen_record, language)


def get_summary_payload(user: User, now: datetime) -> dict[str, dict[str, object]]:
    """Return due and unseen counts for each supported study language."""
    summary: dict[str, dict[str, object]] = {}
    for language in StudyLanguage.values:
        summary[language] = {
            "due": due_progress_queryset(user, language, now).count(),
            "label": StudyLanguage(language).label,
            "unseen": unseen_records_queryset(user, language).count(),
        }
    return summary


def apply_sm2_review(
    progress: StudyProgress,
    grade: str,
    reviewed_at: datetime,
) -> None:
    """Update a study progress row using the SM-2 algorithm."""
    quality = STUDY_QUALITY_BY_GRADE[grade]
    prior_repetition = progress.repetition
    prior_interval = progress.interval_days
    prior_easiness_factor = progress.easiness_factor or INITIAL_EASINESS_FACTOR

    if quality < 3:
        progress.repetition = 0
        progress.interval_days = 1
    else:
        if prior_repetition == 0:
            progress.interval_days = 1
        elif prior_repetition == 1:
            progress.interval_days = 6
        else:
            progress.interval_days = max(1, round(prior_interval * prior_easiness_factor))
        progress.repetition = prior_repetition + 1
        progress.successful_reviews += 1

    easiness_factor_delta = 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
    progress.easiness_factor = max(
        MIN_EASINESS_FACTOR,
        prior_easiness_factor + easiness_factor_delta,
    )
    progress.due_at = reviewed_at + timedelta(days=progress.interval_days)
    progress.last_grade = grade
    progress.last_quality = quality
    progress.last_reviewed_at = reviewed_at
    progress.total_reviews += 1


class StudySummaryView(APIView):
    """Return study counts for each language."""

    def get(self, request: Request) -> Response:
        """Return due and unseen counts for the current user."""
        return Response({"summary": get_summary_payload(request.user, timezone.now())})


class StudyNextCardView(APIView):
    """Return the next due or unseen card for a language."""

    def get(self, request: Request) -> Response:
        """Return the next card payload or an empty state."""
        serializer = StudyLanguageQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        language = cast(str, serializer.validated_data["language"])
        card = get_next_card(request.user, language, timezone.now())
        return Response({"card": card})


class StudyReviewView(APIView):
    """Apply a study review and return the next card."""

    def post(self, request: Request) -> Response:
        """Persist a review grade for a study card."""
        serializer = StudyReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        record_id = cast(int, serializer.validated_data["record_id"])
        language = cast(str, serializer.validated_data["language"])
        grade = cast(str, serializer.validated_data["grade"])
        now = timezone.now()

        record = get_object_or_404(
            eligible_records_queryset(request.user, language),
            pk=record_id,
        )

        with transaction.atomic():
            progress, _created = (
                StudyProgress.objects.select_for_update().get_or_create(
                    user=request.user,
                    record=record,
                    language=language,
                    defaults={"due_at": now},
                )
            )
            apply_sm2_review(progress, grade, now)
            progress.save()
            next_card = get_next_card(request.user, language, now)

        return Response(
            {
                "next_card": next_card,
                "review": {
                    "due_at": progress.due_at,
                    "easiness_factor": progress.easiness_factor,
                    "grade": grade,
                    "interval_days": progress.interval_days,
                    "language": language,
                    "quality": progress.last_quality,
                    "record_id": record_id,
                    "repetition": progress.repetition,
                },
            }
        )
