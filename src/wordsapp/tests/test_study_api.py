"""Tests for study API endpoints."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from wordsapp.models import PartOfSpeech, Record, StudyLanguage, StudyProgress, User, Word


@pytest.fixture
def api_client() -> APIClient:
    """Create an API client."""
    return APIClient()


@pytest.fixture
def user(db) -> User:
    """Create a study user."""
    return User.objects.create_user(username="learner", password="password")


@pytest.fixture
def other_user(db) -> User:
    """Create another user."""
    return User.objects.create_user(username="other", password="password")


@pytest.fixture
def noun(db) -> PartOfSpeech:
    """Create a noun part of speech."""
    return PartOfSpeech.objects.create(name="noun", abbreviation="n")


@pytest.fixture
def blank_abbreviation_pos(db) -> PartOfSpeech:
    """Create a part of speech with an empty abbreviation."""
    return PartOfSpeech.objects.create(name="mystery", abbreviation="")


def create_record(
    *,
    owner: User,
    part_of_speech: PartOfSpeech,
    comment: str = "",
    en: str,
    ru: str,
    fr: str,
    frequency: int,
) -> Record:
    """Create a word and record pair."""
    word = Word.objects.create(
        user_added=owner,
        en=en,
        ru=ru,
        fr=fr,
        part_of_speech=part_of_speech,
        frequency=frequency,
        comment=comment,
    )
    return Record.objects.create(user=owner, word=word)


@pytest.mark.django_db
def test_study_summary_counts_due_and_unseen_cards(
    api_client: APIClient,
    user: User,
    other_user: User,
    noun: PartOfSpeech,
) -> None:
    """The summary endpoint should count due and unseen cards per language."""
    due_record = create_record(
        owner=user,
        part_of_speech=noun,
        en="cat",
        ru="кот",
        fr="chat",
        frequency=10,
    )
    unseen_record = create_record(
        owner=user,
        part_of_speech=noun,
        en="dog",
        ru="собака",
        fr="chien",
        frequency=20,
    )
    english_only_record = create_record(
        owner=user,
        part_of_speech=noun,
        en="sun",
        ru="солнце",
        fr="",
        frequency=30,
    )
    create_record(
        owner=user,
        part_of_speech=noun,
        en="ghost",
        ru="призрак",
        fr="fantome",
        frequency=40,
    )
    create_record(
        owner=other_user,
        part_of_speech=noun,
        en="other",
        ru="другой",
        fr="autre",
        frequency=1,
    )

    now = timezone.now()
    StudyProgress.objects.create(
        user=user,
        record=due_record,
        language=StudyLanguage.ENGLISH,
        due_at=now - timedelta(days=1),
    )
    StudyProgress.objects.create(
        user=user,
        record=unseen_record,
        language=StudyLanguage.FRENCH,
        due_at=now + timedelta(days=1),
    )

    api_client.force_authenticate(user=user)
    response = api_client.get("/study/summary/")

    assert response.status_code == 200
    assert response.json() == {
        "summary": {
            "en": {"due": 1, "label": "English", "unseen": 3},
            "fr": {"due": 0, "label": "French", "unseen": 2},
        }
    }

    assert english_only_record.pk is not None


@pytest.mark.django_db
def test_next_card_prefers_due_cards_and_formats_prompt(
    api_client: APIClient,
    user: User,
    noun: PartOfSpeech,
) -> None:
    """Due cards should be returned before unseen cards."""
    due_record = create_record(
        owner=user,
        part_of_speech=noun,
        en="cat",
        ru="кот",
        fr="chat",
        frequency=50,
    )
    create_record(
        owner=user,
        part_of_speech=noun,
        en="apple",
        ru="яблоко",
        fr="pomme",
        frequency=1,
    )
    StudyProgress.objects.create(
        user=user,
        record=due_record,
        language=StudyLanguage.ENGLISH,
        due_at=timezone.now() - timedelta(hours=2),
    )

    api_client.force_authenticate(user=user)
    response = api_client.get("/study/next-card/", {"language": "en"})

    assert response.status_code == 200
    assert response.json() == {
        "card": {
            "answer": "кот",
            "comment": "",
            "language": "en",
            "part_of_speech_abbreviation": "n",
            "prompt": "cat (n)",
            "record_id": due_record.pk,
        }
    }


@pytest.mark.django_db
def test_next_card_includes_comment_in_prompt_when_present(
    api_client: APIClient,
    user: User,
    noun: PartOfSpeech,
) -> None:
    """Prompt should append the word comment when present."""
    record = create_record(
        owner=user,
        part_of_speech=noun,
        comment="domestic animal",
        en="Cat",
        ru="кот",
        fr="chat",
        frequency=10,
    )

    api_client.force_authenticate(user=user)
    response = api_client.get("/study/next-card/", {"language": "en"})

    assert response.status_code == 200
    assert response.json() == {
        "card": {
            "answer": "кот",
            "comment": "domestic animal",
            "language": "en",
            "part_of_speech_abbreviation": "n",
            "prompt": "Cat (n) - domestic animal",
            "record_id": record.pk,
        }
    }


@pytest.mark.django_db
def test_next_card_skips_ineligible_records_and_orders_unseen_by_frequency(
    api_client: APIClient,
    user: User,
    noun: PartOfSpeech,
    blank_abbreviation_pos: PartOfSpeech,
) -> None:
    """Only eligible records should be returned, ordered by frequency."""
    low_frequency_record = create_record(
        owner=user,
        part_of_speech=noun,
        en="bird",
        ru="птица",
        fr="oiseau",
        frequency=5,
    )
    create_record(
        owner=user,
        part_of_speech=noun,
        en="house",
        ru="",
        fr="maison",
        frequency=1,
    )
    create_record(
        owner=user,
        part_of_speech=noun,
        en="river",
        ru="река",
        fr="",
        frequency=2,
    )
    create_record(
        owner=user,
        part_of_speech=blank_abbreviation_pos,
        en="stone",
        ru="камень",
        fr="pierre",
        frequency=3,
    )
    create_record(
        owner=user,
        part_of_speech=noun,
        en="tree",
        ru="дерево",
        fr="arbre",
        frequency=8,
    )

    api_client.force_authenticate(user=user)
    response = api_client.get("/study/next-card/", {"language": "fr"})

    assert response.status_code == 200
    assert response.json()["card"]["record_id"] == low_frequency_record.pk
    assert response.json()["card"]["prompt"] == "oiseau (n)"


@pytest.mark.django_db
def test_review_creates_progress_and_returns_next_card(
    api_client: APIClient,
    user: User,
    noun: PartOfSpeech,
) -> None:
    """Submitting a review should create SM-2 progress and return the next card."""
    reviewed_record = create_record(
        owner=user,
        part_of_speech=noun,
        en="cat",
        ru="кот",
        fr="chat",
        frequency=10,
    )
    next_record = create_record(
        owner=user,
        part_of_speech=noun,
        en="dog",
        ru="собака",
        fr="chien",
        frequency=20,
    )

    api_client.force_authenticate(user=user)
    before_request = timezone.now()
    response = api_client.post(
        "/study/review/",
        {"grade": "easy", "language": "en", "record_id": reviewed_record.pk},
        format="json",
    )
    after_request = timezone.now()

    assert response.status_code == 200
    payload = response.json()
    assert payload["next_card"]["record_id"] == next_record.pk
    assert payload["review"]["grade"] == "easy"
    assert payload["review"]["interval_days"] == 1
    assert payload["review"]["quality"] == 5
    assert payload["review"]["repetition"] == 1
    assert payload["review"]["easiness_factor"] == pytest.approx(2.6)

    progress = StudyProgress.objects.get(
        user=user,
        record=reviewed_record,
        language=StudyLanguage.ENGLISH,
    )
    assert progress.repetition == 1
    assert progress.interval_days == 1
    assert progress.total_reviews == 1
    assert progress.successful_reviews == 1
    assert (
        before_request + timedelta(days=1)
        <= progress.due_at
        <= after_request + timedelta(days=1)
    )


@pytest.mark.django_db
def test_review_again_resets_sm2_progress(
    api_client: APIClient,
    user: User,
    noun: PartOfSpeech,
) -> None:
    """An Again review should reset repetition and interval."""
    record = create_record(
        owner=user,
        part_of_speech=noun,
        en="cat",
        ru="кот",
        fr="chat",
        frequency=10,
    )
    progress = StudyProgress.objects.create(
        user=user,
        record=record,
        language=StudyLanguage.ENGLISH,
        repetition=2,
        interval_days=6,
        easiness_factor=2.6,
        due_at=timezone.now() - timedelta(days=1),
        total_reviews=3,
        successful_reviews=2,
    )

    api_client.force_authenticate(user=user)
    response = api_client.post(
        "/study/review/",
        {"grade": "again", "language": "en", "record_id": record.pk},
        format="json",
    )

    assert response.status_code == 200
    progress.refresh_from_db()
    assert progress.repetition == 0
    assert progress.interval_days == 1
    assert progress.last_quality == 2
    assert progress.last_grade == "again"
    assert progress.easiness_factor == pytest.approx(2.28)
    assert progress.total_reviews == 4
    assert progress.successful_reviews == 2


@pytest.mark.django_db
def test_study_progress_is_independent_per_language(
    api_client: APIClient,
    user: User,
    noun: PartOfSpeech,
) -> None:
    """Reviewing English should not create French progress for the same record."""
    record = create_record(
        owner=user,
        part_of_speech=noun,
        en="cat",
        ru="кот",
        fr="chat",
        frequency=10,
    )

    api_client.force_authenticate(user=user)
    review_response = api_client.post(
        "/study/review/",
        {"grade": "hard", "language": "en", "record_id": record.pk},
        format="json",
    )
    next_card_response = api_client.get("/study/next-card/", {"language": "fr"})

    assert review_response.status_code == 200
    assert next_card_response.status_code == 200
    assert next_card_response.json()["card"]["record_id"] == record.pk
    assert StudyProgress.objects.filter(user=user, record=record).count() == 1
