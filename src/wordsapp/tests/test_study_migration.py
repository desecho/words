"""Tests for study-grade data migrations."""

from __future__ import annotations

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone


@pytest.mark.django_db(transaction=True)
def test_binary_study_grade_migration_maps_existing_values() -> None:
    """Legacy study grades should be remapped to the new binary values."""
    old_target = [("wordsapp", "0006_word_comment")]
    new_target = [("wordsapp", "0007_binary_study_grades")]

    executor = MigrationExecutor(connection)
    executor.migrate(old_target)
    old_apps = executor.loader.project_state(old_target).apps

    User = old_apps.get_model("wordsapp", "User")
    PartOfSpeech = old_apps.get_model("wordsapp", "PartOfSpeech")
    Word = old_apps.get_model("wordsapp", "Word")
    Record = old_apps.get_model("wordsapp", "Record")
    StudyProgress = old_apps.get_model("wordsapp", "StudyProgress")

    user = User.objects.create(username="learner")
    noun = PartOfSpeech.objects.create(name="noun", abbreviation="n")

    created_progress_ids: list[int] = []
    for index, (grade, language) in enumerate(
        [("again", "en"), ("hard", "fr"), ("easy", "en")],
        start=1,
    ):
        word = Word.objects.create(
            user_added=user,
            en=f"word-{index}",
            fr=f"mot-{index}",
            ru=f"слово-{index}",
            part_of_speech=noun,
        )
        record = Record.objects.create(user=user, word=word)
        progress = StudyProgress.objects.create(
            user=user,
            record=record,
            language=language,
            due_at=timezone.now(),
            last_grade=grade,
        )
        created_progress_ids.append(progress.pk)

    executor = MigrationExecutor(connection)
    executor.migrate(new_target)
    new_apps = executor.loader.project_state(new_target).apps
    NewStudyProgress = new_apps.get_model("wordsapp", "StudyProgress")

    migrated_grades = list(
        NewStudyProgress.objects.filter(pk__in=created_progress_ids)
        .order_by("pk")
        .values_list("last_grade", flat=True)
    )

    assert migrated_grades == ["incorrect", "correct", "correct"]
