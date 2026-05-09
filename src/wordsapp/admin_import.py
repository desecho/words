"""Admin views for importing words."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, TypeAlias

from django import forms
from django.contrib import admin, messages
from django.core.files.uploadedfile import UploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from wordsapp.models import Word

if TYPE_CHECKING:
    ImportWordsFormBase: TypeAlias = forms.Form
else:
    ImportWordsFormBase = forms.Form


class ImportWordsForm(ImportWordsFormBase):
    """Form for uploading a word import workbook."""

    workbook = forms.FileField(
        label="Workbook",
        help_text="Upload an .xlsx workbook with headers: frequency, word, pos, word_ru, word_fr.",
    )

    def clean_workbook(self) -> UploadedFile:
        """Validate that the uploaded file has the expected workbook extension."""
        workbook = self.cleaned_data["workbook"]
        if not isinstance(workbook, UploadedFile):
            raise forms.ValidationError("Upload a workbook file.")

        workbook_name = workbook.name or ""
        if Path(workbook_name).suffix.lower() != ".xlsx":
            raise forms.ValidationError("Upload an .xlsx workbook.")

        return workbook


def import_words_admin_view(request: HttpRequest) -> HttpResponse:
    """Upload a workbook and import it using the import_words command."""
    if request.method == "POST":
        form = ImportWordsForm(request.POST, request.FILES)
        if form.is_valid():
            workbook = form.cleaned_data["workbook"]
            stdout = StringIO()
            temp_path: Path | None = None

            try:
                with NamedTemporaryFile(suffix=".xlsx", delete=False) as temp_file:
                    temp_path = Path(temp_file.name)
                    for chunk in workbook.chunks():
                        temp_file.write(chunk)

                call_command("import_words", workbook_path=str(temp_path), stdout=stdout)
            except CommandError as exc:
                messages.error(request, str(exc))
            else:
                output = stdout.getvalue().strip() or "Imported words."
                messages.success(request, output)
                return redirect("wordsapp_import_words")
            finally:
                if temp_path is not None:
                    temp_path.unlink(missing_ok=True)
    else:
        form = ImportWordsForm()

    context = {
        **admin.site.each_context(request),
        "form": form,
        "opts": Word._meta,
        "title": "Import words",
    }
    return render(request, "admin/import_words.html", context)
