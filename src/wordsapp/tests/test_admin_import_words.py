"""Tests for importing words through the Django admin."""

from __future__ import annotations

from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from openpyxl import Workbook  # type: ignore[import-untyped]

from wordsapp.models import PartOfSpeech, Record, User, Word

POS_NAME_BY_ABBREVIATION = {
    "v": "verb",
    "n": "noun",
    "r": "adverb",
    "j": "adjective",
    "u": "interjection",
    "pro": "pronoun",
    "pre": "preposition",
    "c": "conjunction",
    "d": "determiner",
}


def build_workbook_upload(
    *,
    headers: list[str],
    rows: list[list[object]],
    name: str = "words.xlsx",
) -> SimpleUploadedFile:
    """Create an uploaded workbook file."""
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(headers)
    for row in rows:
        worksheet.append(row)

    output = BytesIO()
    workbook.save(output)
    workbook.close()
    output.seek(0)

    return SimpleUploadedFile(
        name,
        output.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@pytest.fixture
def admin_client(db) -> Client:
    """Create a logged-in admin client backed by the import user."""
    user = User.objects.create_superuser(
        id=1,
        username="admin",
        password="password",
        email="admin@example.com",
    )
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def part_of_speech_map(db) -> dict[str, PartOfSpeech]:
    """Create part of speech records used by the import."""
    created: dict[str, PartOfSpeech] = {}
    for name in POS_NAME_BY_ABBREVIATION.values():
        created[name] = PartOfSpeech.objects.create(
            name=name,
            abbreviation=name[:3],
        )
    return created


@pytest.mark.django_db
def test_admin_index_links_to_import_words(admin_client: Client) -> None:
    """The admin dashboard should link to the import page."""
    response = admin_client.get("/admin/")

    assert response.status_code == 200
    assert b"Import words" in response.content
    assert b"/admin/import-words/" in response.content


@pytest.mark.django_db
def test_admin_import_words_page_requires_staff() -> None:
    """Anonymous users should be redirected through admin login."""
    client = Client()

    response = client.get("/admin/import-words/")

    assert response.status_code == 302
    assert response.url == "/admin/login/?next=/admin/import-words/"


@pytest.mark.django_db
def test_admin_import_words_page_rejects_non_staff_user() -> None:
    """Authenticated non-staff users should not access the admin import page."""
    user = User.objects.create_user(username="user", password="password")
    client = Client()
    client.force_login(user)

    response = client.get("/admin/import-words/")

    assert response.status_code == 302
    assert response.url == "/admin/login/?next=/admin/import-words/"


@pytest.mark.django_db
def test_admin_import_words_page_renders_for_admin(admin_client: Client) -> None:
    """Staff admins should be able to open the import page."""
    response = admin_client.get("/admin/import-words/")

    assert response.status_code == 200
    assert b"Import words" in response.content
    assert b'name="workbook"' in response.content


@pytest.mark.django_db
def test_admin_import_words_upload_imports_workbook(
    admin_client: Client,
    part_of_speech_map: dict[str, PartOfSpeech],
) -> None:
    """Uploading a valid workbook should import words and records."""
    upload = build_workbook_upload(
        headers=["frequency", "word", "pos", "word_ru", "word_fr"],
        rows=[[1, "be", "v", "быть", "etre"]],
    )

    response = admin_client.post(
        "/admin/import-words/",
        {"workbook": upload},
        follow=True,
    )

    assert response.status_code == 200
    assert b"Imported 1 words" in response.content
    assert Word.objects.count() == 1
    assert Record.objects.count() == 1

    word = Word.objects.get()
    record = Record.objects.get()
    assert word.user_added_id == 1
    assert word.part_of_speech_id == part_of_speech_map["verb"].pk
    assert word.en == "be"
    assert word.ru == "быть"
    assert word.fr == "etre"
    assert record.user_id == 1
    assert record.word_id == word.pk


@pytest.mark.django_db
def test_admin_import_words_upload_shows_command_errors(
    admin_client: Client,
    part_of_speech_map: dict[str, PartOfSpeech],
) -> None:
    """Command validation errors should be shown without importing rows."""
    upload = build_workbook_upload(
        headers=["frequency", "word", "pos", "word_ru", "word_fr"],
        rows=[[1, "be", "x", "быть", "etre"]],
    )

    response = admin_client.post("/admin/import-words/", {"workbook": upload})

    assert response.status_code == 200
    assert b"Row 2: unknown pos abbreviation &#x27;x&#x27;." in response.content
    assert Word.objects.count() == 0
    assert Record.objects.count() == 0


@pytest.mark.django_db
def test_admin_import_words_upload_rejects_non_xlsx(admin_client: Client) -> None:
    """Non-xlsx uploads should fail form validation before import."""
    upload = SimpleUploadedFile("words.txt", b"not a workbook", content_type="text/plain")

    response = admin_client.post("/admin/import-words/", {"workbook": upload})

    assert response.status_code == 200
    assert b"Upload an .xlsx workbook." in response.content
    assert Word.objects.count() == 0
    assert Record.objects.count() == 0
