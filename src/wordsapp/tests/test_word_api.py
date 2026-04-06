"""Tests for word-creation API endpoints."""

from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient

from wordsapp.models import PartOfSpeech, Record, StudyProgress, User, Word


@pytest.fixture
def api_client() -> APIClient:
    """Create an API client."""
    return APIClient()


@pytest.fixture
def user(db) -> User:
    """Create an authenticated user."""
    return User.objects.create_user(username="creator", password="password")


@pytest.fixture
def other_user(db) -> User:
    """Create another authenticated user."""
    return User.objects.create_user(username="other", password="password")


@pytest.fixture
def noun(db) -> PartOfSpeech:
    """Create a noun part of speech."""
    return PartOfSpeech.objects.create(name="noun", abbreviation="n")


@pytest.fixture
def verb(db) -> PartOfSpeech:
    """Create a verb part of speech."""
    return PartOfSpeech.objects.create(name="verb", abbreviation="v")


def create_word(
    *,
    owner: User,
    part_of_speech: PartOfSpeech,
    en: str,
    ru: str,
    fr: str = "",
    comment: str = "",
) -> Word:
    """Create a word."""
    return Word.objects.create(
        user_added=owner,
        en=en,
        fr=fr,
        ru=ru,
        comment=comment,
        part_of_speech=part_of_speech,
    )


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
            "date_added": response.json()["word"]["date_added"],
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


@pytest.mark.django_db
def test_word_model_validation_requires_russian(
    user: User,
    noun: PartOfSpeech,
) -> None:
    """Model validation should reject blank Russian translations."""
    word = Word(
        user_added=user,
        en="cat",
        fr="chat",
        ru="",
        part_of_speech=noun,
    )

    with pytest.raises(ValidationError) as exc_info:
        word.full_clean()

    assert exc_info.value.message_dict == {"ru": ["This field cannot be blank."]}


@pytest.mark.django_db
def test_word_model_requires_english_or_french(
    user: User,
    noun: PartOfSpeech,
) -> None:
    """The database should reject words with neither English nor French."""
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Word.objects.create(
                user_added=user,
                en="",
                fr="",
                ru="кот",
                part_of_speech=noun,
            )


@pytest.mark.django_db
def test_word_list_returns_only_current_user_words_in_reverse_chronological_order(
    api_client: APIClient,
    user: User,
    other_user: User,
    noun: PartOfSpeech,
    verb: PartOfSpeech,
) -> None:
    """The words list should show only the authenticated user's words."""
    first_word = create_word(
        owner=user,
        part_of_speech=noun,
        en="cat",
        ru="кот",
        comment="animal",
    )
    second_word = create_word(
        owner=user,
        part_of_speech=verb,
        en="run",
        fr="courir",
        ru="бежать",
    )
    create_word(
        owner=other_user,
        part_of_speech=noun,
        en="hidden",
        ru="скрытый",
    )

    api_client.force_authenticate(user=user)
    response = api_client.get("/words/")

    assert response.status_code == 200
    assert response.json()["words"] == [
        {
            "comment": "",
            "date_added": response.json()["words"][0]["date_added"],
            "en": "run",
            "fr": "courir",
            "id": second_word.pk,
            "part_of_speech": {
                "abbreviation": "v",
                "id": verb.pk,
                "name": "verb",
            },
            "ru": "бежать",
        },
        {
            "comment": "animal",
            "date_added": response.json()["words"][1]["date_added"],
            "en": "cat",
            "fr": "",
            "id": first_word.pk,
            "part_of_speech": {
                "abbreviation": "n",
                "id": noun.pk,
                "name": "noun",
            },
            "ru": "кот",
        },
    ]


@pytest.mark.django_db
def test_word_list_search_matches_only_translation_fields(
    api_client: APIClient,
    user: User,
    noun: PartOfSpeech,
) -> None:
    """Search should filter by translation fields but not comment."""
    russian_match = create_word(
        owner=user,
        part_of_speech=noun,
        en="cat",
        ru="кот",
        comment="pet animal",
    )
    english_match = create_word(
        owner=user,
        part_of_speech=noun,
        en="dog",
        fr="chien",
        ru="пёс",
    )
    create_word(
        owner=user,
        part_of_speech=noun,
        en="bird",
        ru="птица",
        comment="contains feline in comment only",
    )

    api_client.force_authenticate(user=user)

    response = api_client.get("/words/", {"search": "кот"})
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["words"]] == [russian_match.pk]

    response = api_client.get("/words/", {"search": "chi"})
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["words"]] == [english_match.pk]

    response = api_client.get("/words/", {"search": "feline"})
    assert response.status_code == 200
    assert response.json()["words"] == []


@pytest.mark.django_db
def test_word_update_updates_current_users_word(
    api_client: APIClient,
    user: User,
    noun: PartOfSpeech,
    verb: PartOfSpeech,
) -> None:
    """Users should be able to edit their own words."""
    word = create_word(
        owner=user,
        part_of_speech=noun,
        en="cat",
        fr="chat",
        ru="кот",
        comment="domestic animal",
    )
    Record.objects.create(user=user, word=word)

    api_client.force_authenticate(user=user)
    response = api_client.patch(
        f"/words/{word.pk}/",
        {
            "comment": "updated",
            "en": "kitten",
            "fr": "",
            "part_of_speech_id": verb.pk,
            "ru": "котёнок",
        },
        format="json",
    )

    assert response.status_code == 200
    word.refresh_from_db()
    assert word.en == "kitten"
    assert word.fr == ""
    assert word.ru == "котёнок"
    assert word.comment == "updated"
    assert word.part_of_speech_id == verb.pk
    assert response.json() == {
        "word": {
            "comment": "updated",
            "date_added": response.json()["word"]["date_added"],
            "en": "kitten",
            "fr": "",
            "id": word.pk,
            "part_of_speech": {
                "abbreviation": "v",
                "id": verb.pk,
                "name": "verb",
            },
            "ru": "котёнок",
        }
    }


@pytest.mark.django_db
def test_word_update_rejects_other_users_word(
    api_client: APIClient,
    user: User,
    other_user: User,
    noun: PartOfSpeech,
) -> None:
    """Users should not be able to edit another user's word."""
    word = create_word(
        owner=other_user,
        part_of_speech=noun,
        en="cat",
        ru="кот",
    )

    api_client.force_authenticate(user=user)
    response = api_client.patch(
        f"/words/{word.pk}/",
        {
            "comment": "",
            "en": "kitten",
            "fr": "",
            "part_of_speech_id": noun.pk,
            "ru": "котёнок",
        },
        format="json",
    )

    assert response.status_code == 404
    word.refresh_from_db()
    assert word.en == "cat"
    assert word.ru == "кот"


@pytest.mark.django_db
def test_word_delete_deletes_word_record_and_study_progress(
    api_client: APIClient,
    user: User,
    noun: PartOfSpeech,
) -> None:
    """Deleting a word should cascade to the linked study data."""
    word = create_word(
        owner=user,
        part_of_speech=noun,
        en="cat",
        ru="кот",
    )
    record = Record.objects.create(user=user, word=word)
    StudyProgress.objects.create(
        user=user,
        record=record,
        language="en",
        due_at="2024-01-01T00:00:00Z",
    )

    api_client.force_authenticate(user=user)
    response = api_client.delete(f"/words/{word.pk}/")

    assert response.status_code == 204
    assert Word.objects.count() == 0
    assert Record.objects.count() == 0
    assert StudyProgress.objects.count() == 0


@pytest.mark.django_db
def test_word_delete_rejects_other_users_word(
    api_client: APIClient,
    user: User,
    other_user: User,
    noun: PartOfSpeech,
) -> None:
    """Users should not be able to delete another user's word."""
    word = create_word(
        owner=other_user,
        part_of_speech=noun,
        en="cat",
        ru="кот",
    )
    Record.objects.create(user=other_user, word=word)

    api_client.force_authenticate(user=user)
    response = api_client.delete(f"/words/{word.pk}/")

    assert response.status_code == 404
    assert Word.objects.count() == 1
    assert Record.objects.count() == 1
