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
              <v-btn
                color="primary"
                :to="`/texts/${text.id}`"
                variant="outlined"
              >
                Open
              </v-btn>
            </div>
            <p class="text-card__preview">
              {{ previewText(text.content) }}
            </p>
          </article>
        </div>
      </section>
    </div>
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
const fieldErrors = ref<TextFormErrors>({
    content: [],
    language: [],
    name: [],
});
const language = ref<StudyLanguage | null>(null);
const loadingTexts = ref(false);
const name = ref("");
const saving = ref(false);
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
  border: 1px solid rgba(91, 63, 45, 0.08);
  background: rgba(255, 255, 255, 0.68);
}

.text-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.text-card__title {
  margin: 0;
  font-size: 1.1rem;
}

.text-card__meta {
  margin-top: 0.25rem;
  color: rgba(30, 27, 24, 0.68);
  font-size: 0.92rem;
}

.text-card__preview {
  margin: 0;
  color: rgba(30, 27, 24, 0.78);
  line-height: 1.6;
}

.texts-empty {
  padding: 1rem 1.1rem;
  border: 1px dashed rgba(91, 63, 45, 0.18);
  color: rgba(30, 27, 24, 0.7);
}

@media (max-width: 720px) {
  .text-card__header,
  .texts-section__header {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
