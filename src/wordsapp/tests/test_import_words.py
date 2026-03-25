"""Tests for the import_words management command."""

from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
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


def build_workbook(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    """Create a workbook for import tests."""
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(headers)
    for row in rows:
        worksheet.append(row)
    workbook.save(path)
    workbook.close()


@pytest.fixture
def import_user(db) -> User:
    """Create the required import user."""
    return User.objects.create_user(id=1, username="importer", password="password")


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
def test_import_words_creates_words_and_records_for_all_pos_mappings(
    tmp_path: Path,
    import_user: User,
    part_of_speech_map: dict[str, PartOfSpeech],
) -> None:
    """The command should import words and create matching records."""
    workbook_path = tmp_path / "import.xlsx"
    rows = [
        [index, f"word-{abbreviation}", abbreviation, f"ru-{abbreviation}", f"fr-{abbreviation}"]
        for index, abbreviation in enumerate(POS_NAME_BY_ABBREVIATION, start=1)
    ]
    build_workbook(
        workbook_path,
        ["frequency", "word", "pos", "word_ru", "word_fr"],
        rows,
    )

    stdout = StringIO()
    call_command("import_words", workbook_path=str(workbook_path), stdout=stdout)

    assert Word.objects.count() == len(POS_NAME_BY_ABBREVIATION)
    assert Record.objects.count() == len(POS_NAME_BY_ABBREVIATION)
    assert all(word.user_added_id == import_user.pk for word in Word.objects.all())
    assert all(record.user_id == import_user.pk for record in Record.objects.all())

    words_by_en = {word.en: word for word in Word.objects.select_related("part_of_speech")}
    for abbreviation, name in POS_NAME_BY_ABBREVIATION.items():
        imported_word = words_by_en[f"word-{abbreviation}"]
        assert imported_word.part_of_speech_id == part_of_speech_map[name].pk
        assert imported_word.ru == f"ru-{abbreviation}"
        assert imported_word.fr == f"fr-{abbreviation}"

    assert "Imported 9 words" in stdout.getvalue()


@pytest.mark.django_db
def test_import_words_uses_default_words_xlsx_path(
    tmp_path: Path,
    import_user: User,
    part_of_speech_map: dict[str, PartOfSpeech],
) -> None:
    """The default workbook path should be <BASE_DIR>/words.xlsx."""
    build_workbook(
        tmp_path / "words.xlsx",
        ["frequency", "word", "pos", "word_ru", "word_fr"],
        [[1, "be", "v", "быть", "etre"]],
    )

    stdout = StringIO()
    with override_settings(BASE_DIR=tmp_path):
        call_command("import_words", stdout=stdout)

    imported_word = Word.objects.get()
    assert imported_word.en == "be"
    assert imported_word.part_of_speech_id == part_of_speech_map["verb"].pk
    assert Record.objects.get().user_id == import_user.pk
    assert "Imported 1 words" in stdout.getvalue()


@pytest.mark.django_db
def test_import_words_fails_when_import_user_is_missing(
    tmp_path: Path,
    part_of_speech_map: dict[str, PartOfSpeech],
) -> None:
    """User id=1 must exist."""
    workbook_path = tmp_path / "import.xlsx"
    build_workbook(
        workbook_path,
        ["frequency", "word", "pos", "word_ru", "word_fr"],
        [[1, "be", "v", "быть", "etre"]],
    )

    with pytest.raises(CommandError, match="User with id=1 does not exist"):
        call_command("import_words", workbook_path=str(workbook_path))

    assert Word.objects.count() == 0
    assert Record.objects.count() == 0


@pytest.mark.django_db
def test_import_words_fails_for_unknown_pos(
    tmp_path: Path,
    import_user: User,
    part_of_speech_map: dict[str, PartOfSpeech],
) -> None:
    """Unknown part of speech abbreviations should abort the import."""
    workbook_path = tmp_path / "import.xlsx"
    build_workbook(
        workbook_path,
        ["frequency", "word", "pos", "word_ru", "word_fr"],
        [[1, "be", "x", "быть", "etre"]],
    )

    with pytest.raises(CommandError, match="unknown pos abbreviation 'x'"):
        call_command("import_words", workbook_path=str(workbook_path))

    assert Word.objects.count() == 0
    assert Record.objects.count() == 0


@pytest.mark.django_db
def test_import_words_fails_for_missing_headers(
    tmp_path: Path,
    import_user: User,
    part_of_speech_map: dict[str, PartOfSpeech],
) -> None:
    """Workbook headers must match the expected import format."""
    workbook_path = tmp_path / "import.xlsx"
    build_workbook(
        workbook_path,
        ["freq", "word", "pos", "word_ru", "word_fr"],
        [[1, "be", "v", "быть", "etre"]],
    )

    with pytest.raises(CommandError, match="Workbook headers must be exactly"):
        call_command("import_words", workbook_path=str(workbook_path))

    assert Word.objects.count() == 0
    assert Record.objects.count() == 0


@pytest.mark.django_db
def test_import_words_fails_for_existing_frequency_conflict(
    tmp_path: Path,
    import_user: User,
    part_of_speech_map: dict[str, PartOfSpeech],
) -> None:
    """Existing frequencies should abort the import."""
    workbook_path = tmp_path / "import.xlsx"
    Word.objects.create(
        user_added=import_user,
        en="already-there",
        ru="уже",
        fr="deja",
        part_of_speech=part_of_speech_map["verb"],
        frequency=1,
    )
    build_workbook(
        workbook_path,
        ["frequency", "word", "pos", "word_ru", "word_fr"],
        [[1, "be", "v", "быть", "etre"]],
    )

    with pytest.raises(CommandError, match="frequency 1 already exists"):
        call_command("import_words", workbook_path=str(workbook_path))

    assert Word.objects.count() == 1
    assert Record.objects.count() == 0


@pytest.mark.django_db
def test_import_words_fails_for_existing_word_and_part_of_speech_conflict(
    tmp_path: Path,
    import_user: User,
    part_of_speech_map: dict[str, PartOfSpeech],
) -> None:
    """Existing word and part-of-speech pairs should abort the import."""
    workbook_path = tmp_path / "import.xlsx"
    Word.objects.create(
        user_added=import_user,
        en="be",
        ru="быть",
        fr="etre",
        part_of_speech=part_of_speech_map["verb"],
        frequency=50,
    )
    build_workbook(
        workbook_path,
        ["frequency", "word", "pos", "word_ru", "word_fr"],
        [[1, "be", "v", "быть", "etre"]],
    )

    with pytest.raises(
        CommandError,
        match="word 'be' with part of speech 'verb' already exists",
    ):
        call_command("import_words", workbook_path=str(workbook_path))

    assert Word.objects.count() == 1
    assert Record.objects.count() == 0


@pytest.mark.django_db
def test_import_words_rolls_back_when_a_later_row_is_invalid(
    tmp_path: Path,
    import_user: User,
    part_of_speech_map: dict[str, PartOfSpeech],
) -> None:
    """Later failures should roll back earlier rows in the same workbook."""
    workbook_path = tmp_path / "import.xlsx"
    build_workbook(
        workbook_path,
        ["frequency", "word", "pos", "word_ru", "word_fr"],
        [
            [1, "be", "v", "быть", "etre"],
            [2, "quickly", "x", "быстро", "vite"],
        ],
    )

    with pytest.raises(CommandError, match="Row 3: unknown pos abbreviation 'x'"):
        call_command("import_words", workbook_path=str(workbook_path))

    assert Word.objects.count() == 0
    assert Record.objects.count() == 0
