"""Tests for text API endpoints."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from wordsapp.models import PartOfSpeech, Record, Text, User, Word


@pytest.fixture
def api_client() -> APIClient:
    """Create an API client."""
    return APIClient()


@pytest.fixture
def user(db) -> User:
    """Create an authenticated user."""
    return User.objects.create_user(username="reader", password="password")


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


def create_record(
    *,
    owner: User,
    part_of_speech: PartOfSpeech,
    en: str,
    fr: str = "",
    ru: str = "translation",
) -> Record:
    """Create a word and record pair."""
    word = Word.objects.create(
        user_added=owner,
        en=en,
        fr=fr,
        ru=ru,
        part_of_speech=part_of_speech,
    )
    return Record.objects.create(user=owner, word=word)


@pytest.mark.django_db
def test_text_list_returns_only_current_user_texts_in_reverse_chronological_order(
    api_client: APIClient,
    user: User,
    other_user: User,
) -> None:
    """The texts list should show only the authenticated user's texts."""
    first_text = Text.objects.create(
        user_added=user,
        name="First",
        language="en",
        content="First content",
    )
    second_text = Text.objects.create(
        user_added=user,
        name="Second",
        language="fr",
        content="Second content",
    )
    Text.objects.create(
        user_added=other_user,
        name="Hidden",
        language="en",
        content="Other content",
    )

    api_client.force_authenticate(user=user)
    response = api_client.get("/texts/")

    assert response.status_code == 200
    assert response.json()["texts"] == [
        {
            "id": second_text.pk,
            "name": "Second",
            "language": "fr",
            "content": "Second content",
            "date_added": response.json()["texts"][0]["date_added"],
        },
        {
            "id": first_text.pk,
            "name": "First",
            "language": "en",
            "content": "First content",
            "date_added": response.json()["texts"][1]["date_added"],
        },
    ]


@pytest.mark.django_db
def test_text_create_creates_text_for_current_user(
    api_client: APIClient,
    user: User,
) -> None:
    """Creating a text from the UI should persist it for the current user."""
    api_client.force_authenticate(user=user)

    response = api_client.post(
        "/texts/",
        {
            "name": "Sky",
            "language": "en",
            "content": "A cat walks in the rain among the stars.",
        },
        format="json",
    )

    assert response.status_code == 201
    assert Text.objects.count() == 1
    text = Text.objects.get()
    assert text.user_added_id == user.pk
    assert text.name == "Sky"
    assert text.language == "en"
    assert text.content == "A cat walks in the rain among the stars."
    assert response.json()["text"] == {
        "id": text.pk,
        "name": "Sky",
        "language": "en",
        "content": "A cat walks in the rain among the stars.",
        "date_added": response.json()["text"]["date_added"],
    }


@pytest.mark.django_db
def test_text_detail_returns_articles_and_matching_records(
    api_client: APIClient,
    user: User,
    noun: PartOfSpeech,
    verb: PartOfSpeech,
) -> None:
    """Text detail should highlight article words and matching record words."""
    walk_record = create_record(owner=user, part_of_speech=verb, en="walk", ru="идти")
    star_record = create_record(owner=user, part_of_speech=noun, en="star", ru="звезда")
    text = Text.objects.create(
        user_added=user,
        name="Sky",
        language="en",
        content="A cat walks in the rain among the stars.",
    )

    api_client.force_authenticate(user=user)
    response = api_client.get(f"/texts/{text.pk}/")

    assert response.status_code == 200
    assert response.json() == {
        "text": {
            "id": text.pk,
            "name": "Sky",
            "language": "en",
            "content": "A cat walks in the rain among the stars.",
            "date_added": response.json()["text"]["date_added"],
        },
        "segments": [
            {
                "type": "match",
                "value": "A",
                "normalized": "a",
                "match_kind": "article",
                "record_id": None,
            },
            {"type": "text", "value": " cat "},
            {
                "type": "match",
                "value": "walks",
                "normalized": "walk",
                "match_kind": "record",
                "record_id": walk_record.pk,
            },
            {"type": "text", "value": " in "},
            {
                "type": "match",
                "value": "the",
                "normalized": "the",
                "match_kind": "article",
                "record_id": None,
            },
            {"type": "text", "value": " rain among "},
            {
                "type": "match",
                "value": "the",
                "normalized": "the",
                "match_kind": "article",
                "record_id": None,
            },
            {"type": "text", "value": " "},
            {
                "type": "match",
                "value": "stars",
                "normalized": "star",
                "match_kind": "record",
                "record_id": star_record.pk,
            },
            {"type": "text", "value": "."},
        ],
    }


@pytest.mark.django_db
def test_text_detail_marks_french_articles(
    api_client: APIClient,
    user: User,
) -> None:
    """French articles should be highlighted even without records."""
    text = Text.objects.create(
        user_added=user,
        name="French",
        language="fr",
        content="L'homme et les etoiles.",
    )

    api_client.force_authenticate(user=user)
    response = api_client.get(f"/texts/{text.pk}/")

    assert response.status_code == 200
    assert response.json()["segments"] == [
        {
            "type": "match",
            "value": "L'",
            "normalized": "l'",
            "match_kind": "article",
            "record_id": None,
        },
        {"type": "text", "value": "homme et "},
        {
            "type": "match",
            "value": "les",
            "normalized": "les",
            "match_kind": "article",
            "record_id": None,
        },
        {"type": "text", "value": " etoiles."},
    ]


@pytest.mark.django_db
def test_text_detail_highlights_english_contractions_and_number_words(
    api_client: APIClient,
    user: User,
) -> None:
    """English contractions and number words should be highlighted automatically."""
    text = Text.objects.create(
        user_added=user,
        name="English automatic",
        language="en",
        content="Don't stop: one, two, three and won't.",
    )

    api_client.force_authenticate(user=user)
    response = api_client.get(f"/texts/{text.pk}/")

    assert response.status_code == 200
    assert response.json()["segments"] == [
        {
            "type": "match",
            "value": "Don't",
            "normalized": "don't",
            "match_kind": "contraction",
            "record_id": None,
        },
        {"type": "text", "value": " stop: "},
        {
            "type": "match",
            "value": "one",
            "normalized": "one",
            "match_kind": "number_word",
            "record_id": None,
        },
        {"type": "text", "value": ", "},
        {
            "type": "match",
            "value": "two",
            "normalized": "two",
            "match_kind": "number_word",
            "record_id": None,
        },
        {"type": "text", "value": ", "},
        {
            "type": "match",
            "value": "three",
            "normalized": "three",
            "match_kind": "number_word",
            "record_id": None,
        },
        {"type": "text", "value": " and "},
        {
            "type": "match",
            "value": "won't",
            "normalized": "won't",
            "match_kind": "contraction",
            "record_id": None,
        },
        {"type": "text", "value": "."},
    ]


@pytest.mark.django_db
def test_text_detail_highlights_french_contractions_and_number_words(
    api_client: APIClient,
    user: User,
) -> None:
    """French apostrophe forms and number words should be highlighted automatically."""
    text = Text.objects.create(
        user_added=user,
        name="French automatic",
        language="fr",
        content="C'est d'accord: deux, trois.",
    )

    api_client.force_authenticate(user=user)
    response = api_client.get(f"/texts/{text.pk}/")

    assert response.status_code == 200
    assert response.json()["segments"] == [
        {
            "type": "match",
            "value": "C'",
            "normalized": "c'",
            "match_kind": "contraction",
            "record_id": None,
        },
        {"type": "text", "value": "est "},
        {
            "type": "match",
            "value": "d'",
            "normalized": "d'",
            "match_kind": "contraction",
            "record_id": None,
        },
        {"type": "text", "value": "accord: "},
        {
            "type": "match",
            "value": "deux",
            "normalized": "deux",
            "match_kind": "number_word",
            "record_id": None,
        },
        {"type": "text", "value": ", "},
        {
            "type": "match",
            "value": "trois",
            "normalized": "trois",
            "match_kind": "number_word",
            "record_id": None,
        },
        {"type": "text", "value": "."},
    ]


@pytest.mark.django_db
def test_text_detail_returns_404_for_other_users_text(
    api_client: APIClient,
    user: User,
    other_user: User,
) -> None:
    """Users should not be able to read another user's text."""
    text = Text.objects.create(
        user_added=other_user,
        name="Private",
        language="en",
        content="Hidden",
    )

    api_client.force_authenticate(user=user)
    response = api_client.get(f"/texts/{text.pk}/")

    assert response.status_code == 404
