"""Tests for word-creation API endpoints."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from wordsapp.models import PartOfSpeech, Record, User, Word


@pytest.fixture
def api_client() -> APIClient:
    """Create an API client."""
    return APIClient()


@pytest.fixture
def user(db) -> User:
    """Create an authenticated user."""
    return User.objects.create_user(username="creator", password="password")


@pytest.fixture
def noun(db) -> PartOfSpeech:
    """Create a noun part of speech."""
    return PartOfSpeech.objects.create(name="noun", abbreviation="n")


@pytest.fixture
def verb(db) -> PartOfSpeech:
    """Create a verb part of speech."""
    return PartOfSpeech.objects.create(name="verb", abbreviation="v")


@pytest.mark.django_db
def test_part_of_speech_list_returns_ordered_options(
    api_client: APIClient,
    user: User,
    noun: PartOfSpeech,
    verb: PartOfSpeech,
) -> None:
    """The add-word form should receive ordered part-of-speech options."""
    api_client.force_authenticate(user=user)

    response = api_client.get("/parts-of-speech/")

    assert response.status_code == 200
    assert response.json() == {
        "parts_of_speech": [
            {"abbreviation": "n", "id": noun.pk, "name": "noun"},
            {"abbreviation": "v", "id": verb.pk, "name": "verb"},
        ]
    }


@pytest.mark.django_db
def test_word_create_creates_word_and_record(
    api_client: APIClient,
    user: User,
    noun: PartOfSpeech,
) -> None:
    """Creating a word from the UI should also create the matching record."""
    api_client.force_authenticate(user=user)

    response = api_client.post(
        "/words/",
        {
            "comment": "domestic animal",
            "en": "cat",
            "fr": "",
            "part_of_speech_id": noun.pk,
            "ru": "кот",
        },
        format="json",
    )

    assert response.status_code == 201
    assert Word.objects.count() == 1
    assert Record.objects.count() == 1

    word = Word.objects.select_related("part_of_speech").get()
    record = Record.objects.get()
    assert word.user_added_id == user.pk
    assert word.frequency is None
    assert word.en == "cat"
    assert word.fr == ""
    assert word.ru == "кот"
    assert word.comment == "domestic animal"
    assert word.part_of_speech_id == noun.pk
    assert record.user_id == user.pk
    assert record.word_id == word.pk
    assert response.json() == {
        "record_id": record.pk,
        "word": {
            "comment": "domestic animal",
            "en": "cat",
            "fr": "",
            "id": word.pk,
            "part_of_speech": {
                "abbreviation": "n",
                "id": noun.pk,
                "name": "noun",
            },
            "ru": "кот",
        },
    }


@pytest.mark.django_db
def test_word_create_requires_russian(
    api_client: APIClient,
    user: User,
    noun: PartOfSpeech,
) -> None:
    """Russian is required."""
    api_client.force_authenticate(user=user)

    response = api_client.post(
        "/words/",
        {
            "en": "cat",
            "fr": "",
            "part_of_speech_id": noun.pk,
            "ru": "",
        },
        format="json",
    )

    assert response.status_code == 400
    assert response.json() == {"ru": ["This field may not be blank."]}
    assert Word.objects.count() == 0
    assert Record.objects.count() == 0


@pytest.mark.django_db
def test_word_create_requires_part_of_speech(
    api_client: APIClient,
    user: User,
) -> None:
    """Part of speech is required."""
    api_client.force_authenticate(user=user)

    response = api_client.post(
        "/words/",
        {
            "en": "cat",
            "fr": "",
            "ru": "кот",
        },
        format="json",
    )

    assert response.status_code == 400
    assert response.json() == {"part_of_speech_id": ["This field is required."]}
    assert Word.objects.count() == 0
    assert Record.objects.count() == 0


@pytest.mark.django_db
def test_word_create_requires_english_or_french(
    api_client: APIClient,
    user: User,
    noun: PartOfSpeech,
) -> None:
    """At least one target-language field is required."""
    api_client.force_authenticate(user=user)

    response = api_client.post(
        "/words/",
        {
            "en": "",
            "fr": "",
            "part_of_speech_id": noun.pk,
            "ru": "кот",
        },
        format="json",
    )

    assert response.status_code == 400
    assert response.json() == {
        "non_field_errors": ["Provide at least one of English or French."]
    }
    assert Word.objects.count() == 0
    assert Record.objects.count() == 0


@pytest.mark.django_db
def test_word_create_allows_duplicate_submissions(
    api_client: APIClient,
    user: User,
    noun: PartOfSpeech,
) -> None:
    """Duplicate submits should create distinct words and records."""
    api_client.force_authenticate(user=user)
    payload = {
        "comment": "domestic animal",
        "en": "cat",
        "fr": "",
        "part_of_speech_id": noun.pk,
        "ru": "кот",
    }

    first_response = api_client.post("/words/", payload, format="json")
    second_response = api_client.post("/words/", payload, format="json")

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert Word.objects.count() == 2
    assert Record.objects.count() == 2
    assert first_response.json()["word"]["id"] != second_response.json()["word"]["id"]
    assert first_response.json()["record_id"] != second_response.json()["record_id"]
