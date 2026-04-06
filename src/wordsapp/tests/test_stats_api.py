"""Tests for stats API endpoints."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from wordsapp.models import PartOfSpeech, Record, StudyLanguage, StudyProgress, Text, User, Word


@pytest.fixture
def api_client() -> APIClient:
    """Create an API client."""
    return APIClient()


@pytest.fixture
def user(db) -> User:
    """Create an authenticated user."""
    return User.objects.create_user(username="stats-user", password="password")


@pytest.fixture
def other_user(db) -> User:
    """Create another authenticated user."""
    return User.objects.create_user(username="other-user", password="password")


@pytest.fixture
def noun(db) -> PartOfSpeech:
    """Create a noun part of speech."""
    return PartOfSpeech.objects.create(name="noun", abbreviation="n")


@pytest.fixture
def verb(db) -> PartOfSpeech:
    """Create a verb part of speech."""
    return PartOfSpeech.objects.create(name="verb", abbreviation="v")


def create_record(
    *,
    owner: User,
    part_of_speech: PartOfSpeech,
    en: str,
    ru: str,
    fr: str = "",
) -> Record:
    """Create a word and matching record."""
    word = Word.objects.create(
        user_added=owner,
        en=en,
        fr=fr,
        ru=ru,
        part_of_speech=part_of_speech,
    )
    return Record.objects.create(user=owner, word=word)


@pytest.mark.django_db
def test_stats_summary_requires_authentication(api_client: APIClient) -> None:
    """The stats dashboard should reject anonymous requests."""
    response = api_client.get("/stats/summary/")

    assert response.status_code == 401


@pytest.mark.django_db
def test_stats_summary_returns_zeroed_dashboard_when_user_has_no_data(
    api_client: APIClient,
    user: User,
) -> None:
    """The stats dashboard should return zero counts for an empty account."""
    api_client.force_authenticate(user=user)

    response = api_client.get("/stats/summary/")

    assert response.status_code == 200
    assert response.json() == {
        "activity": {
            "recent_reviews_7d": 0,
            "recent_texts_added_7d": 0,
            "recent_words_added_7d": 0,
        },
        "collection": {
            "language_coverage": {
                "with_both": 0,
                "with_english": 0,
                "with_french": 0,
            },
            "parts_of_speech": [],
        },
        "overview": {
            "records_total": 0,
            "review_success_rate": 0.0,
            "reviews_successful": 0,
            "reviews_total": 0,
            "texts_total": 0,
            "words_total": 0,
        },
        "study": {
            "en": {
                "active": 0,
                "due": 0,
                "ignored": 0,
                "label": "English",
                "reviewed_total": 0,
                "success_rate": 0.0,
                "successful_reviews": 0,
                "unseen": 0,
            },
            "fr": {
                "active": 0,
                "due": 0,
                "ignored": 0,
                "label": "French",
                "reviewed_total": 0,
                "success_rate": 0.0,
                "successful_reviews": 0,
                "unseen": 0,
            },
        },
    }


@pytest.mark.django_db
def test_stats_summary_aggregates_dashboard_metrics_for_current_user(
    api_client: APIClient,
    user: User,
    other_user: User,
    noun: PartOfSpeech,
    verb: PartOfSpeech,
) -> None:
    """The stats dashboard should aggregate only the authenticated user's data."""
    now = timezone.now()

    english_due_record = create_record(
        owner=user,
        part_of_speech=noun,
        en="cat",
        ru="кот",
        fr="chat",
    )
    english_unseen_record = create_record(
        owner=user,
        part_of_speech=noun,
        en="dog",
        ru="собака",
        fr="chien",
    )
    reviewed_record = create_record(
        owner=user,
        part_of_speech=verb,
        en="run",
        ru="бежать",
        fr="courir",
    )
    french_ignored_record = create_record(
        owner=user,
        part_of_speech=noun,
        en="house",
        ru="дом",
        fr="maison",
    )
    old_record = create_record(
        owner=user,
        part_of_speech=noun,
        en="sun",
        ru="солнце",
        fr="",
    )
    other_record = create_record(
        owner=other_user,
        part_of_speech=noun,
        en="other",
        ru="другой",
        fr="autre",
    )

    recent_text = Text.objects.create(
        user_added=user,
        name="Recent text",
        language=StudyLanguage.ENGLISH,
        content="Recent content",
    )
    old_text = Text.objects.create(
        user_added=user,
        name="Old text",
        language=StudyLanguage.FRENCH,
        content="Old content",
    )
    Text.objects.create(
        user_added=other_user,
        name="Other text",
        language=StudyLanguage.ENGLISH,
        content="Other content",
    )

    Word.objects.filter(pk=old_record.word_id).update(date_added=now - timedelta(days=8))
    Text.objects.filter(pk=old_text.pk).update(date_added=now - timedelta(days=8))

    StudyProgress.objects.create(
        user=user,
        record=english_due_record,
        language=StudyLanguage.ENGLISH,
        due_at=now - timedelta(days=1),
        total_reviews=2,
        successful_reviews=1,
        last_reviewed_at=now - timedelta(days=1),
    )
    StudyProgress.objects.create(
        user=user,
        record=reviewed_record,
        language=StudyLanguage.ENGLISH,
        due_at=now + timedelta(days=3),
        total_reviews=3,
        successful_reviews=3,
        last_reviewed_at=now - timedelta(days=2),
    )
    StudyProgress.objects.create(
        user=user,
        record=reviewed_record,
        language=StudyLanguage.FRENCH,
        due_at=now + timedelta(days=2),
        total_reviews=0,
        successful_reviews=0,
    )
    StudyProgress.objects.create(
        user=user,
        record=french_ignored_record,
        language=StudyLanguage.FRENCH,
        due_at=now - timedelta(days=1),
        ignore=True,
        last_reviewed_at=now - timedelta(days=3),
    )
    StudyProgress.objects.create(
        user=other_user,
        record=other_record,
        language=StudyLanguage.ENGLISH,
        due_at=now - timedelta(days=1),
        total_reviews=7,
        successful_reviews=6,
        last_reviewed_at=now - timedelta(days=1),
    )

    api_client.force_authenticate(user=user)
    response = api_client.get("/stats/summary/")

    assert response.status_code == 200
    assert response.json() == {
        "activity": {
            "recent_reviews_7d": 3,
            "recent_texts_added_7d": 1,
            "recent_words_added_7d": 4,
        },
        "collection": {
            "language_coverage": {
                "with_both": 4,
                "with_english": 5,
                "with_french": 4,
            },
            "parts_of_speech": [
                {"count": 4, "label": "noun (n)"},
                {"count": 1, "label": "verb (v)"},
            ],
        },
        "overview": {
            "records_total": 5,
            "review_success_rate": 80.0,
            "reviews_successful": 4,
            "reviews_total": 5,
            "texts_total": 2,
            "words_total": 5,
        },
        "study": {
            "en": {
                "active": 2,
                "due": 1,
                "ignored": 0,
                "label": "English",
                "reviewed_total": 5,
                "success_rate": 80.0,
                "successful_reviews": 4,
                "unseen": 3,
            },
            "fr": {
                "active": 1,
                "due": 0,
                "ignored": 1,
                "label": "French",
                "reviewed_total": 0,
                "success_rate": 0.0,
                "successful_reviews": 0,
                "unseen": 2,
            },
        },
    }

    assert recent_text.pk is not None
    assert english_unseen_record.pk is not None
