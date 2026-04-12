<template>
  <PagePanel
    eyebrow="Study"
    title="Flashcards for English and French"
    description="Pick a language, reveal the Russian translation, and grade your recall so SM-2 can schedule the next review."
  >
    <div class="study-layout">
      <div class="study-language-grid">
        <button
          v-for="option in languageOptions"
          :key="option.code"
          class="study-language"
          :class="{ 'study-language--active': selectedLanguage === option.code }"
          type="button"
          @click="selectedLanguage = option.code"
        >
          <div class="study-language__header">
            <span class="study-language__title">{{ option.title }}</span>
            <span class="study-language__cue">{{ option.cue }}</span>
          </div>
          <div class="study-language__meta">
            <span>{{ summary[option.code].due }} due</span>
            <span>{{ summary[option.code].unseen }} unseen</span>
          </div>
        </button>
      </div>

      <div class="study-card-shell">
        <div class="study-card-shell__topline">
          <div class="study-card-shell__label">
            {{ summary[selectedLanguage].label }} prompt
          </div>
          <div class="study-card-shell__counts">
            <span>{{ summary[selectedLanguage].due }} due</span>
            <span>{{ summary[selectedLanguage].unseen }} unseen</span>
          </div>
        </div>

        <div v-if="loadingCard" class="study-status">
          Loading the next card...
        </div>

        <template v-else-if="card">
          <v-sheet class="study-card" elevation="0">
            <div class="study-card__prompt">{{ card.prompt }}</div>
            <div class="study-card__instruction">
              Think of the Russian meaning before you reveal it.
            </div>

            <div v-if="revealed" class="study-card__answer">
              {{ card.answer }}
            </div>
            <div v-else class="study-card__answer study-card__answer--hidden">
              Translation hidden
            </div>
          </v-sheet>

          <div class="study-shortcuts" aria-label="Keyboard shortcuts">
            <span class="study-shortcuts__label">Shortcuts</span>
            <span class="study-shortcuts__item">
              <kbd class="study-shortcut-key">Space</kbd>
              Show translation
            </span>
            <span
              v-for="grade in gradeOptions"
              :key="grade.value"
              class="study-shortcuts__item"
            >
              <kbd class="study-shortcut-key">{{ grade.shortcut }}</kbd>
              {{ grade.label }}
            </span>
          </div>

          <div class="study-actions">
            <v-btn
              color="primary"
              :disabled="reviewLoading"
              size="large"
              variant="flat"
              @click="revealed = true"
            >
              <span class="study-button-content">
                <span>Show translation</span>
                <kbd class="study-shortcut-key">Space</kbd>
              </span>
            </v-btn>
            <v-btn
              v-for="grade in gradeOptions"
              :key="grade.value"
              :color="grade.color"
              :disabled="isGradeDisabled(grade)"
              :loading="reviewLoading && pendingGrade === grade.value"
              size="large"
              :variant="grade.variant"
              @click="submitGrade(grade.value)"
            >
              <span class="study-button-content">
                <span>{{ grade.label }}</span>
                <kbd class="study-shortcut-key">{{ grade.shortcut }}</kbd>
              </span>
            </v-btn>
          </div>
        </template>

        <v-sheet v-else class="study-empty" elevation="0">
          <div class="study-empty__title">No cards are available right now.</div>
          <p>
            This language has no due or unseen study cards yet. Add more eligible
            records or come back when the next reviews are due.
          </p>
        </v-sheet>
      </div>
    </div>
  </PagePanel>
</template>

<script lang="ts" setup>
import axios from "axios";
import { computed, onMounted, onUnmounted, ref, watch } from "vue";

import type {
    StudyCard,
    StudyCardResponse,
    StudyGrade,
    StudyLanguage,
    StudyReviewResponse,
    StudySummary,
} from "../types";

import PagePanel from "../components/PagePanel.vue";
import { getUrl } from "../helpers";
import { $toast } from "../toast";

const languageOptions: Array<{
    code: StudyLanguage;
    cue: string;
    title: string;
}> = [
    {
        code: "en",
        cue: "English -> Russian",
        title: "English",
    },
    {
        code: "fr",
        cue: "French -> Russian",
        title: "French",
    },
];

const gradeOptions: Array<{
    color: string;
    label: string;
    requiresIgnoreableCard: boolean;
    shortcut: string;
    value: StudyGrade;
    variant: "flat" | "outlined";
}> = [
    {
        color: "primary",
        label: "Incorrect",
        requiresIgnoreableCard: false,
        shortcut: "1",
        value: "incorrect",
        variant: "outlined",
    },
    {
        color: "secondary",
        label: "Correct",
        requiresIgnoreableCard: false,
        shortcut: "2",
        value: "correct",
        variant: "flat",
    },
    {
        color: "secondary",
        label: "Ignore",
        requiresIgnoreableCard: true,
        shortcut: "3",
        value: "ignore",
        variant: "outlined",
    },
];

const selectedLanguage = ref<StudyLanguage>("en");
const card = ref<StudyCard | null>(null);
const loadingCard = ref(false);
const pendingGrade = ref<StudyGrade | null>(null);
const revealed = ref(false);
const summary = ref<StudySummary["summary"]>({
    en: { due: 0, label: "English", unseen: 0 },
    fr: { due: 0, label: "French", unseen: 0 },
});

const reviewLoading = computed(() => pendingGrade.value !== null);

async function loadSummary(showErrorToast = true): Promise<void> {
    try {
        const response = await axios.get(getUrl("study/summary/"));
        const data = response.data as StudySummary;
        summary.value = data.summary;
    } catch (error: unknown) {
        console.error(error);
        if (showErrorToast) {
            $toast.error("Unable to load study counts.");
        }
    }
}

async function loadCard(language: StudyLanguage): Promise<void> {
    loadingCard.value = true;
    revealed.value = false;
    const requestedLanguage = language;

    try {
        const response = await axios.get(getUrl("study/next-card/"), {
            params: { language },
        });
        const data = response.data as StudyCardResponse;
        if (selectedLanguage.value === requestedLanguage) {
            card.value = data.card;
        }
    } catch (error: unknown) {
        console.error(error);
        if (selectedLanguage.value === requestedLanguage) {
            card.value = null;
        }
        $toast.error("Unable to load the next study card.");
    } finally {
        if (selectedLanguage.value === requestedLanguage) {
            loadingCard.value = false;
        }
    }
}

function reviewableCardForGrade(grade: StudyGrade): StudyCard | null {
    if (card.value === null || !revealed.value || reviewLoading.value) {
        return null;
    }
    if (grade === "ignore" && !card.value.can_ignore) {
        return null;
    }

    return card.value;
}

async function submitGrade(grade: StudyGrade): Promise<void> {
    const reviewCard = reviewableCardForGrade(grade);
    if (reviewCard === null) {
        return;
    }

    const recordIdKey = "record_id";
    const reviewLanguage = selectedLanguage.value;
    pendingGrade.value = grade;

    try {
        const response = await axios.post(getUrl("study/review/"), {
            grade,
            language: reviewLanguage,
            [recordIdKey]: reviewCard.record_id,
        });
        const data = response.data as StudyReviewResponse;
        if (selectedLanguage.value === reviewLanguage) {
            card.value = data.next_card;
            revealed.value = false;
        }
        await loadSummary(false);
    } catch (error: unknown) {
        console.error(error);
        $toast.error("Unable to save the study result.");
    } finally {
        pendingGrade.value = null;
    }
}

watch(selectedLanguage, async (language, previousLanguage) => {
    if (language === previousLanguage) {
        return;
    }
    await loadCard(language);
});

function isGradeDisabled(
    grade: (typeof gradeOptions)[number],
): boolean {
    return (
        !revealed.value ||
        reviewLoading.value ||
        (grade.requiresIgnoreableCard && card.value?.can_ignore === false)
    );
}

function isEditableTarget(target: EventTarget | null): boolean {
    if (!(target instanceof HTMLElement)) {
        return false;
    }

    return (
        target.isContentEditable ||
        ["INPUT", "SELECT", "TEXTAREA"].includes(target.tagName)
    );
}

function isButtonActivationTarget(target: EventTarget | null): boolean {
    return (
        target instanceof HTMLElement &&
        target.closest("a, button, [role='button']") !== null
    );
}

function handleStudyShortcut(event: KeyboardEvent): void {
    if (
        isEditableTarget(event.target) ||
        event.altKey ||
        event.ctrlKey ||
        event.metaKey ||
        event.shiftKey
    ) {
        return;
    }

    if (event.code === "Space" || event.key === " " || event.key === "Spacebar") {
        if (isButtonActivationTarget(event.target)) {
            return;
        }

        if (card.value === null || loadingCard.value) {
            return;
        }

        event.preventDefault();

        if (!revealed.value && !reviewLoading.value) {
            revealed.value = true;
        }

        return;
    }

    const grade = gradeOptions.find((option) => option.shortcut === event.key);
    if (grade === undefined || card.value === null) {
        return;
    }

    event.preventDefault();

    if (!isGradeDisabled(grade)) {
        void submitGrade(grade.value);
    }
}

onMounted(async () => {
    window.addEventListener("keydown", handleStudyShortcut);
    await Promise.all([loadSummary(), loadCard(selectedLanguage.value)]);
});

onUnmounted(() => {
    window.removeEventListener("keydown", handleStudyShortcut);
});
</script>

<style scoped>
.study-layout {
  display: grid;
  gap: 1.5rem;
}

.study-language-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.study-language {
  display: grid;
  gap: 0.9rem;
  padding: 1.15rem 1.25rem;
  border: 1px solid var(--card-border);
  border-radius: 1.5rem;
  background: var(--card-gradient);
  cursor: pointer;
  font: inherit;
  text-align: left;
  transition:
    transform 140ms ease,
    border-color 140ms ease,
    box-shadow 140ms ease;
}

.study-language:hover {
  transform: translateY(-2px);
  border-color: rgba(var(--v-theme-primary), 0.28);
  box-shadow: var(--shadow-card-hover);
}

.study-language--active {
  border-color: rgba(var(--v-theme-secondary), 0.45);
  box-shadow: var(--shadow-card-active);
}

.study-language__header {
  display: grid;
  gap: 0.35rem;
}

.study-language__title {
  font-family: "Iowan Old Style", "Palatino Linotype", serif;
  font-size: 1.35rem;
  line-height: 1.1;
}

.study-language__cue {
  color: var(--app-text-soft);
  font-size: 0.95rem;
}

.study-language__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  color: rgb(var(--v-theme-primary));
  font-size: 0.92rem;
  font-weight: 600;
}

.study-card-shell {
  display: grid;
  gap: 1rem;
}

.study-card-shell__topline {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: center;
}

.study-card-shell__label {
  color: rgb(var(--v-theme-primary));
  font-size: 0.84rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.study-card-shell__counts {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  color: var(--app-text-soft);
  font-size: 0.95rem;
}

.study-card {
  display: grid;
  gap: 1rem;
  padding: clamp(1.5rem, 5vw, 2.5rem);
  border: 1px solid var(--card-border);
  border-radius: 2rem;
  background: var(--study-card-bg);
}

.study-card__prompt {
  font-family: "Iowan Old Style", "Palatino Linotype", serif;
  font-size: clamp(2rem, 6vw, 3.4rem);
  line-height: 1.04;
}

.study-card__instruction {
  color: var(--app-text-soft);
  font-size: 1rem;
}

.study-card__answer {
  min-height: 4.5rem;
  padding: 1rem 1.15rem;
  border-radius: 1.25rem;
  background: rgba(var(--v-theme-secondary), 0.14);
  color: rgb(var(--v-theme-secondary));
  font-size: clamp(1.35rem, 4vw, 1.8rem);
  font-weight: 600;
}

.study-card__answer--hidden {
  background: var(--hidden-bg);
  color: var(--app-text-faint);
}

.study-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.study-button-content,
.study-shortcuts,
.study-shortcuts__item {
  display: inline-flex;
  align-items: center;
}

.study-button-content {
  gap: 0.45rem;
}

.study-shortcuts {
  flex-wrap: wrap;
  gap: 0.55rem 0.9rem;
  color: var(--app-text-soft);
  font-size: 0.92rem;
}

.study-shortcuts__label {
  color: var(--app-text-muted);
  font-weight: 700;
}

.study-shortcuts__item {
  gap: 0.4rem;
}

.study-shortcut-key {
  display: inline-flex;
  min-width: 1.55rem;
  min-height: 1.45rem;
  align-items: center;
  justify-content: center;
  padding: 0 0.4rem;
  border: 1px solid currentColor;
  border-radius: 0.35rem;
  font-family: inherit;
  font-size: 0.78rem;
  font-weight: 700;
  line-height: 1;
  opacity: 0.78;
}

.study-status,
.study-empty {
  padding: 1.5rem;
  border: 1px dashed var(--empty-border);
  border-radius: 1.5rem;
  background: var(--empty-bg);
}

.study-status {
  color: var(--app-text-soft);
}

.study-empty__title {
  font-family: "Iowan Old Style", "Palatino Linotype", serif;
  font-size: 1.35rem;
}

.study-empty p {
  margin: 0.75rem 0 0;
  color: var(--app-text-muted);
  line-height: 1.6;
}

@media (max-width: 720px) {
  .study-language-grid {
    grid-template-columns: 1fr;
  }

  .study-card__prompt {
    font-size: clamp(1.8rem, 9vw, 2.8rem);
  }
}
</style>
