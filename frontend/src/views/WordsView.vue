<template>
  <PagePanel
    eyebrow="Words"
    title="Words"
    description="Search, edit, and remove the words you've added."
  >
    <section class="words-section">
      <div class="words-section__header">
        <h2 class="words-section__title">Your words</h2>
        <div class="words-section__actions">
          <v-btn
            color="primary"
            to="/words/new"
            variant="flat"
          >
            Add word
          </v-btn>
          <v-btn
            size="small"
            variant="text"
            :disabled="loadingWords"
            :loading="loadingWords"
            @click="loadWords"
          >
            Refresh
          </v-btn>
        </div>
      </div>

      <v-text-field
        v-model="searchQuery"
        clearable
        hide-details
        label="Search Russian, English, or French"
        :loading="loadingWords"
      />

      <div v-if="loadingWords && words.length === 0" class="words-empty">
        Loading words...
      </div>
      <div v-else-if="words.length === 0" class="words-empty">
        {{ wordsEmptyMessage }}
      </div>
      <div v-else class="words-list">
        <article
          v-for="word in words"
          :key="word.id"
          class="word-card"
        >
          <div class="word-card__header">
            <div>
              <h3 class="word-card__title">{{ word.ru }}</h3>
              <div class="word-card__meta">
                {{ formatPartOfSpeech(word.part_of_speech) }} · {{ formatDate(word.date_added) }}
              </div>
            </div>
            <div class="word-card__actions">
              <v-btn
                variant="outlined"
                :disabled="deletingWordId !== null || savingEdit"
                @click="openEditDialog(word)"
              >
                Edit
              </v-btn>
              <v-btn
                color="error"
                variant="text"
                :disabled="deletingWordId !== null || savingEdit"
                :loading="deletingWordId === word.id"
                @click="openDeleteDialog(word)"
              >
                Delete
              </v-btn>
            </div>
          </div>

          <div class="word-card__translations">
            <div class="translation-chip">
              <span class="translation-chip__label">RU</span>
              <span class="translation-chip__value">{{ word.ru }}</span>
            </div>
            <div class="translation-chip">
              <span class="translation-chip__label">EN</span>
              <span class="translation-chip__value">{{ word.en || "-" }}</span>
            </div>
            <div class="translation-chip">
              <span class="translation-chip__label">FR</span>
              <span class="translation-chip__value">{{ word.fr || "-" }}</span>
            </div>
          </div>

          <p v-if="word.comment" class="word-card__comment">
            {{ word.comment }}
          </p>
        </article>
      </div>
    </section>

    <v-dialog
      max-width="560"
      :model-value="editDialogOpen"
      :persistent="savingEdit"
      @update:model-value="onEditDialogModelValueChange"
    >
      <v-card>
        <v-card-title>Edit word</v-card-title>
        <v-card-text>
          <v-form id="edit-word-form" class="form-stack" @submit.prevent="onSaveEdit">
            <v-text-field
              v-model="editForm.ru"
              label="Russian"
              :error-messages="editFieldErrors.ru"
            />
            <v-text-field
              v-model="editForm.en"
              label="English"
              :error-messages="editFieldErrors.en"
            />
            <v-text-field
              v-model="editForm.fr"
              label="French"
              :error-messages="editFieldErrors.fr"
            />
            <v-select
              v-model="editForm.part_of_speech_id"
              :disabled="loadingOptions || savingEdit"
              :error-messages="editFieldErrors.part_of_speech_id"
              :items="partOfSpeechItems"
              item-title="label"
              item-value="id"
              label="Part of speech"
            />
            <v-text-field
              v-model="editForm.comment"
              label="Comment"
              :error-messages="editFieldErrors.comment"
            />

            <div v-if="editFieldErrors.non_field_errors.length > 0" class="form-error">
              {{ editFieldErrors.non_field_errors[0] }}
            </div>
          </v-form>
        </v-card-text>
        <v-card-actions class="dialog-actions">
          <v-spacer />
          <v-btn
            variant="text"
            :disabled="savingEdit"
            @click="closeEditDialog"
          >
            Cancel
          </v-btn>
          <v-btn
            color="primary"
            form="edit-word-form"
            :loading="savingEdit"
            type="submit"
            variant="flat"
          >
            Save changes
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog
      max-width="480"
      :model-value="wordPendingDeletion !== null"
      :persistent="deletingWordId !== null"
      @update:model-value="onDeleteDialogModelValueChange"
    >
      <v-card>
        <v-card-title>Delete word?</v-card-title>
        <v-card-text v-if="wordPendingDeletion">
          Delete "{{ wordPendingDeletion.ru }}" permanently? Its linked study record and progress will be removed too.
        </v-card-text>
        <v-card-actions class="dialog-actions">
          <v-spacer />
          <v-btn
            variant="text"
            :disabled="deletingWordId !== null"
            @click="closeDeleteDialog"
          >
            Cancel
          </v-btn>
          <v-btn
            color="error"
            :disabled="wordPendingDeletion === null"
            :loading="deletingWordId !== null"
            variant="flat"
            @click="onConfirmDelete"
          >
            Delete
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </PagePanel>
</template>

<script lang="ts" setup>
import axios, { isAxiosError } from "axios";
import {
    computed,
    onBeforeUnmount,
    onMounted,
    reactive,
    ref,
    watch,
} from "vue";

import type { Ref } from "vue";
import type {
    PartOfSpeechListResponse,
    PartOfSpeechOption,
    UpdateWordRequest,
    WordItem,
    WordListResponse,
    WordResponse,
} from "../types";

import PagePanel from "../components/PagePanel.vue";
import { getUrl } from "../helpers";
import { $toast } from "../toast";

type WordFormErrors = {
    comment: string[];
    en: string[];
    fr: string[];
    non_field_errors: string[];
    part_of_speech_id: string[];
    ru: string[];
};

type WordFormState = {
    comment: string;
    en: string;
    fr: string;
    part_of_speech_id: number | null;
    ru: string;
};

const editForm = reactive<WordFormState>(createEmptyWordForm());
const editFieldErrors = ref<WordFormErrors>(createEmptyWordFormErrors());
const deletingWordId = ref<number | null>(null);
const editDialogOpen = ref(false);
const editingWordId = ref<number | null>(null);
const loadingOptions = ref(false);
const loadingWords = ref(false);
const partOfSpeechOptions = ref<PartOfSpeechOption[]>([]);
const savingEdit = ref(false);
const searchQuery = ref<string | null>("");
const wordPendingDeletion = ref<WordItem | null>(null);
const words = ref<WordItem[]>([]);

const partOfSpeechItems = computed(() =>
    partOfSpeechOptions.value.map((option) => ({
        ...option,
        label: `${option.name} (${option.abbreviation})`,
    })),
);
const normalizedSearchQuery = computed(() => searchQuery.value?.trim() ?? "");
const wordsEmptyMessage = computed(() =>
    normalizedSearchQuery.value.length > 0
        ? "No words match this search."
        : "No words yet. Add one to start building your list.",
);

let latestLoadWordsRequestId = 0;
let searchTimer: ReturnType<typeof window.setTimeout> | null = null;

function createEmptyWordForm(): WordFormState {
    return {
        comment: "",
        en: "",
        fr: "",
        part_of_speech_id: null,
        ru: "",
    };
}

function createEmptyWordFormErrors(): WordFormErrors {
    return {
        comment: [],
        en: [],
        fr: [],
        non_field_errors: [],
        part_of_speech_id: [],
        ru: [],
    };
}

function resetFieldErrors(fieldErrors: Ref<WordFormErrors>): void {
    fieldErrors.value = createEmptyWordFormErrors();
}

function resetWordForm(form: WordFormState): void {
    Object.assign(form, createEmptyWordForm());
}

function populateWordForm(form: WordFormState, word: WordItem): void {
    Object.assign(form, {
        comment: word.comment,
        en: word.en,
        fr: word.fr,
        part_of_speech_id: word.part_of_speech.id,
        ru: word.ru,
    });
}

function validateWordForm(
    form: WordFormState,
    fieldErrors: Ref<WordFormErrors>,
): boolean {
    resetFieldErrors(fieldErrors);

    if (form.ru.trim().length === 0) {
        fieldErrors.value.ru = ["Russian is required."];
    }
    if (form.part_of_speech_id === null) {
        fieldErrors.value.part_of_speech_id = ["Part of speech is required."];
    }
    if (form.en.trim().length === 0 && form.fr.trim().length === 0) {
        fieldErrors.value.non_field_errors = [
            "Provide at least one of English or French.",
        ];
    }

    return Object.values(fieldErrors.value).every((messages) => messages.length === 0);
}

function applyServerErrors(
    errorData: Record<string, unknown>,
    fieldErrors: Ref<WordFormErrors>,
): void {
    resetFieldErrors(fieldErrors);

    for (const [key, value] of Object.entries(errorData)) {
        if (!Array.isArray(value)) {
            continue;
        }
        const messages = value.filter((item): item is string => typeof item === "string");
        if (key in fieldErrors.value) {
            fieldErrors.value[key as keyof WordFormErrors] = messages;
        }
    }
}

function buildWordPayload(form: WordFormState): UpdateWordRequest {
    return {
        comment: form.comment.trim(),
        en: form.en.trim(),
        fr: form.fr.trim(),
        part_of_speech_id: form.part_of_speech_id,
        ru: form.ru.trim(),
    };
}

function formatDate(value: string): string {
    return new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
    }).format(new Date(value));
}

function formatPartOfSpeech(option: PartOfSpeechOption): string {
    return `${option.name} (${option.abbreviation})`;
}

async function loadPartOfSpeechOptions(): Promise<void> {
    loadingOptions.value = true;

    try {
        const response = await axios.get(getUrl("parts-of-speech/"));
        const data = response.data as PartOfSpeechListResponse;
        partOfSpeechOptions.value = data.parts_of_speech;
    } catch (error: unknown) {
        console.error(error);
        $toast.error("Unable to load parts of speech.");
    } finally {
        loadingOptions.value = false;
    }
}

async function loadWords(): Promise<void> {
    const requestId = latestLoadWordsRequestId + 1;
    latestLoadWordsRequestId = requestId;
    loadingWords.value = true;

    try {
        const search = normalizedSearchQuery.value;
        const response = await axios.get(getUrl("words/"), {
            params: search.length > 0 ? { search } : {},
        });
        const data = response.data as WordListResponse;
        if (requestId === latestLoadWordsRequestId) {
            words.value = data.words;
        }
    } catch (error: unknown) {
        console.error(error);
        if (requestId === latestLoadWordsRequestId) {
            $toast.error("Unable to load words.");
        }
    } finally {
        if (requestId === latestLoadWordsRequestId) {
            loadingWords.value = false;
        }
    }
}

function openEditDialog(word: WordItem): void {
    if (savingEdit.value || deletingWordId.value !== null) {
        return;
    }

    editingWordId.value = word.id;
    populateWordForm(editForm, word);
    resetFieldErrors(editFieldErrors);
    editDialogOpen.value = true;
}

function closeEditDialog(force = false): void {
    if (savingEdit.value && !force) {
        return;
    }

    editDialogOpen.value = false;
    editingWordId.value = null;
    resetWordForm(editForm);
    resetFieldErrors(editFieldErrors);
}

function onEditDialogModelValueChange(value: boolean): void {
    if (!value) {
        closeEditDialog();
    }
}

function openDeleteDialog(word: WordItem): void {
    if (deletingWordId.value !== null || savingEdit.value) {
        return;
    }

    wordPendingDeletion.value = word;
}

function closeDeleteDialog(): void {
    if (deletingWordId.value !== null) {
        return;
    }

    wordPendingDeletion.value = null;
}

function onDeleteDialogModelValueChange(value: boolean): void {
    if (!value) {
        closeDeleteDialog();
    }
}

async function onSaveEdit(): Promise<void> {
    if (editingWordId.value === null) {
        return;
    }
    if (!validateWordForm(editForm, editFieldErrors)) {
        return;
    }

    savingEdit.value = true;

    try {
        const response = await axios.patch<WordResponse>(
            getUrl(`words/${editingWordId.value}/`),
            buildWordPayload(editForm),
        );

        if (normalizedSearchQuery.value.length === 0) {
            words.value = words.value.map((word) =>
                word.id === response.data.word.id ? response.data.word : word,
            );
        } else {
            await loadWords();
        }

        closeEditDialog(true);
        $toast.success("Word updated.");
    } catch (error: unknown) {
        console.error(error);
        if (isAxiosError(error) && error.response?.data) {
            applyServerErrors(error.response.data as Record<string, unknown>, editFieldErrors);
        } else {
            $toast.error("Unable to update the word.");
        }
    } finally {
        savingEdit.value = false;
    }
}

async function onConfirmDelete(): Promise<void> {
    if (wordPendingDeletion.value === null) {
        return;
    }

    const wordToDelete = wordPendingDeletion.value;
    deletingWordId.value = wordToDelete.id;

    try {
        await axios.delete(getUrl(`words/${wordToDelete.id}/`));
        words.value = words.value.filter((word) => word.id !== wordToDelete.id);

        if (editingWordId.value === wordToDelete.id) {
            closeEditDialog();
        }

        wordPendingDeletion.value = null;
        $toast.success("Word deleted.");
    } catch (error: unknown) {
        console.error(error);
        $toast.error("Unable to delete the word.");
    } finally {
        deletingWordId.value = null;
    }
}

watch(searchQuery, () => {
    if (searchTimer !== null) {
        window.clearTimeout(searchTimer);
    }

    searchTimer = window.setTimeout(() => {
        void loadWords();
    }, 250);
});

onMounted(async () => {
    await Promise.all([loadPartOfSpeechOptions(), loadWords()]);
});

onBeforeUnmount(() => {
    if (searchTimer !== null) {
        window.clearTimeout(searchTimer);
    }
});
</script>

<style scoped>
.words-section {
  display: grid;
  gap: 1rem;
}

.words-section__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.words-section__title {
  margin: 0;
  font-family: "Iowan Old Style", "Palatino Linotype", serif;
  font-size: 1.35rem;
}

.words-section__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 0.75rem;
}

.words-list {
  display: grid;
  gap: 1rem;
}

.word-card {
  display: grid;
  gap: 1rem;
  padding: 1.15rem;
  border: 1px solid var(--card-border);
  background: var(--card-bg);
}

.word-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.word-card__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.55rem;
}

.word-card__title {
  margin: 0;
  font-size: 1.1rem;
}

.word-card__meta {
  margin-top: 0.25rem;
  color: var(--app-text-soft);
  font-size: 0.92rem;
}

.word-card__translations {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.75rem;
}

.translation-chip {
  display: grid;
  gap: 0.3rem;
  padding: 0.8rem 0.9rem;
  background: var(--subtle-bg);
}

.translation-chip__label {
  color: var(--app-text-faint);
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.translation-chip__value {
  font-size: 1rem;
  line-height: 1.4;
}

.word-card__comment {
  margin: 0;
  color: var(--app-text-muted);
  line-height: 1.6;
}

.words-empty {
  padding: 1rem 1.1rem;
  border: 1px dashed var(--empty-border);
  background: var(--empty-bg);
  color: var(--app-text-soft);
}

.form-error {
  padding: 0.9rem 1rem;
  border-radius: 1rem;
  background: rgba(var(--v-theme-primary), 0.12);
  color: rgb(var(--v-theme-primary));
  line-height: 1.5;
}

.dialog-actions {
  padding: 0 1rem 1rem;
}

@media (max-width: 720px) {
  .word-card__header,
  .words-section__header {
    flex-direction: column;
    align-items: stretch;
  }

  .word-card__actions,
  .words-section__actions {
    justify-content: flex-start;
  }

  .word-card__translations {
    grid-template-columns: 1fr;
  }
}
</style>
