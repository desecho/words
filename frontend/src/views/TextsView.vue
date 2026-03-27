<template>
  <PagePanel
    eyebrow="Texts"
    title="Texts and word matches"
    description="Create a text, keep your reading material together, and open any text to highlight words that already exist in your account."
  >
    <div class="texts-layout">
      <section class="texts-section">
        <h2 class="texts-section__title">Add a text</h2>
        <v-form class="form-stack" @submit.prevent="onSubmit">
          <v-text-field
            v-model="name"
            label="Name"
            :error-messages="fieldErrors.name"
          />
          <v-select
            v-model="language"
            :error-messages="fieldErrors.language"
            :items="languageItems"
            item-title="label"
            item-value="value"
            label="Language"
          />
          <v-textarea
            v-model="content"
            auto-grow
            label="Content"
            min-rows="6"
            :error-messages="fieldErrors.content"
          />

          <div class="action-row">
            <v-btn
              type="button"
              variant="outlined"
              :disabled="saving || content.trim().length === 0"
              @click="onProcessSubtitles"
            >
              Process subtitles
            </v-btn>
            <v-btn
              color="primary"
              :disabled="saving"
              :loading="saving"
              type="submit"
              variant="flat"
            >
              Save text
            </v-btn>
          </div>
        </v-form>
      </section>

      <section class="texts-section">
        <div class="texts-section__header">
          <h2 class="texts-section__title">Your texts</h2>
          <v-btn
            size="small"
            variant="text"
            :disabled="loadingTexts"
            :loading="loadingTexts"
            @click="loadTexts"
          >
            Refresh
          </v-btn>
        </div>

        <div v-if="loadingTexts" class="texts-empty">
          Loading texts...
        </div>
        <div v-else-if="texts.length === 0" class="texts-empty">
          No texts yet. Add one to start processing it.
        </div>
        <div v-else class="texts-list">
          <article
            v-for="text in texts"
            :key="text.id"
            class="text-card"
          >
            <div class="text-card__header">
              <div>
                <h3 class="text-card__title">{{ text.name }}</h3>
                <div class="text-card__meta">
                  {{ languageLabelByCode[text.language] }} · {{ formatDate(text.date_added) }}
                </div>
              </div>
              <div class="text-card__actions">
                <v-btn
                  color="primary"
                  :disabled="deletingTextId !== null"
                  :to="`/texts/${text.id}`"
                  variant="outlined"
                >
                  Open
                </v-btn>
                <v-btn
                  color="error"
                  :disabled="deletingTextId !== null"
                  :loading="deletingTextId === text.id"
                  variant="text"
                  @click="openDeleteDialog(text)"
                >
                  Delete
                </v-btn>
              </div>
            </div>
            <p class="text-card__preview">
              {{ previewText(text.content) }}
            </p>
          </article>
        </div>
      </section>
    </div>

    <v-dialog
      max-width="480"
      :model-value="textPendingDeletion !== null"
      :persistent="deletingTextId !== null"
      @update:model-value="onDeleteDialogModelValueChange"
    >
      <v-card>
        <v-card-title>Delete text?</v-card-title>
        <v-card-text v-if="textPendingDeletion">
          Delete "{{ textPendingDeletion.name }}" permanently? This cannot be undone.
        </v-card-text>
        <v-card-actions class="delete-dialog__actions">
          <v-spacer />
          <v-btn
            variant="text"
            :disabled="deletingTextId !== null"
            @click="closeDeleteDialog"
          >
            Cancel
          </v-btn>
          <v-btn
            color="error"
            :disabled="textPendingDeletion === null"
            :loading="deletingTextId !== null"
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
import { onMounted, ref } from "vue";

import type {
    CreateTextRequest,
    StudyLanguage,
    TextItem,
    TextListResponse,
    TextResponse,
} from "../types";

import PagePanel from "../components/PagePanel.vue";
import { getUrl } from "../helpers";
import { router } from "../router";
import { $toast } from "../toast";
import { processSubtitleText } from "../utils/subtitles";

type TextFormErrors = {
    content: string[];
    language: string[];
    name: string[];
};

const languageItems: Array<{ label: string; value: StudyLanguage }> = [
    { label: "English", value: "en" },
    { label: "French", value: "fr" },
];
const languageLabelByCode: Record<StudyLanguage, string> = {
    en: "English",
    fr: "French",
};

const content = ref("");
const deletingTextId = ref<number | null>(null);
const fieldErrors = ref<TextFormErrors>({
    content: [],
    language: [],
    name: [],
});
const language = ref<StudyLanguage | null>(null);
const loadingTexts = ref(false);
const name = ref("");
const saving = ref(false);
const textPendingDeletion = ref<TextItem | null>(null);
const texts = ref<TextItem[]>([]);

function resetFieldErrors(): void {
    fieldErrors.value = {
        content: [],
        language: [],
        name: [],
    };
}

function validateForm(): boolean {
    resetFieldErrors();

    if (name.value.trim().length === 0) {
        fieldErrors.value.name = ["Name is required."];
    }
    if (language.value === null) {
        fieldErrors.value.language = ["Language is required."];
    }
    if (content.value.trim().length === 0) {
        fieldErrors.value.content = ["Content is required."];
    }

    return Object.values(fieldErrors.value).every((messages) => messages.length === 0);
}

function applyServerErrors(errorData: Record<string, unknown>): void {
    resetFieldErrors();

    for (const [key, value] of Object.entries(errorData)) {
        if (!Array.isArray(value)) {
            continue;
        }
        const messages = value.filter((item): item is string => typeof item === "string");
        if (key in fieldErrors.value) {
            fieldErrors.value[key as keyof TextFormErrors] = messages;
        }
    }
}

function formatDate(value: string): string {
    return new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
    }).format(new Date(value));
}

function previewText(value: string): string {
    const normalized = value.replace(/\s+/gu, " ").trim();
    if (normalized.length <= 180) {
        return normalized;
    }
    return `${normalized.slice(0, 177)}...`;
}

function onProcessSubtitles(): void {
    const processedContent = processSubtitleText(content.value);

    if (processedContent.length === 0) {
        $toast.error("No subtitle text found to process.");
        return;
    }

    content.value = processedContent;
    fieldErrors.value.content = [];
    $toast.success("Subtitles processed.");
}

function openDeleteDialog(text: TextItem): void {
    if (deletingTextId.value !== null) {
        return;
    }
    textPendingDeletion.value = text;
}

function closeDeleteDialog(): void {
    if (deletingTextId.value !== null) {
        return;
    }
    textPendingDeletion.value = null;
}

function onDeleteDialogModelValueChange(value: boolean): void {
    if (!value) {
        closeDeleteDialog();
    }
}

async function loadTexts(): Promise<void> {
    loadingTexts.value = true;

    try {
        const response = await axios.get(getUrl("texts/"));
        const data = response.data as TextListResponse;
        texts.value = data.texts;
    } catch (error: unknown) {
        console.error(error);
        $toast.error("Unable to load texts.");
    } finally {
        loadingTexts.value = false;
    }
}

async function onConfirmDelete(): Promise<void> {
    if (textPendingDeletion.value === null) {
        return;
    }

    const textToDelete = textPendingDeletion.value;
    deletingTextId.value = textToDelete.id;

    try {
        await axios.delete(getUrl(`texts/${textToDelete.id}/`));
        texts.value = texts.value.filter((text) => text.id !== textToDelete.id);
        textPendingDeletion.value = null;
        $toast.success("Text deleted.");
    } catch (error: unknown) {
        console.error(error);
        $toast.error("Unable to delete the text.");
    } finally {
        deletingTextId.value = null;
    }
}

async function onSubmit(): Promise<void> {
    if (!validateForm() || language.value === null) {
        return;
    }

    saving.value = true;

    try {
        const payload: CreateTextRequest = {
            content: content.value.trim(),
            language: language.value,
            name: name.value.trim(),
        };
        const response = await axios.post<TextResponse>(getUrl("texts/"), payload);
        await loadTexts();
        $toast.success("Text saved.");
        await router.push(`/texts/${response.data.text.id}`);
    } catch (error: unknown) {
        console.error(error);
        if (isAxiosError(error) && error.response?.data) {
            applyServerErrors(error.response.data as Record<string, unknown>);
        } else {
            $toast.error("Unable to save the text.");
        }
    } finally {
        saving.value = false;
    }
}

onMounted(async () => {
    await loadTexts();
});
</script>

<style scoped>
.texts-layout {
  display: grid;
  gap: 2rem;
}

.texts-section {
  display: grid;
  gap: 1rem;
}

.texts-section__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.texts-section__title {
  margin: 0;
  font-family: "Iowan Old Style", "Palatino Linotype", serif;
  font-size: 1.35rem;
}

.texts-list {
  display: grid;
  gap: 1rem;
}

.text-card {
  display: grid;
  gap: 1rem;
  padding: 1.15rem;
  border: 1px solid var(--card-border);
  background: var(--card-bg);
}

.text-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.text-card__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.55rem;
}

.text-card__title {
  margin: 0;
  font-size: 1.1rem;
}

.text-card__meta {
  margin-top: 0.25rem;
  color: var(--app-text-soft);
  font-size: 0.92rem;
}

.text-card__preview {
  margin: 0;
  color: var(--app-text-muted);
  line-height: 1.6;
}

.texts-empty {
  padding: 1rem 1.1rem;
  border: 1px dashed var(--empty-border);
  background: var(--empty-bg);
  color: var(--app-text-soft);
}

.delete-dialog__actions {
  padding: 0 1rem 1rem;
}

@media (max-width: 720px) {
  .text-card__header,
  .texts-section__header {
    flex-direction: column;
    align-items: stretch;
  }

  .text-card__actions {
    justify-content: flex-start;
  }
}
</style>
