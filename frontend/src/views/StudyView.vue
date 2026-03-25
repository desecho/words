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

          <div class="study-actions">
            <v-btn
              color="primary"
              :disabled="reviewLoading"
              size="large"
              variant="flat"
              @click="revealed = true"
            >
              Show translation
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
              {{ grade.label }}
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
import { computed, onMounted, ref, watch } from "vue";

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
    value: StudyGrade;
    variant: "flat" | "outlined";
}> = [
    {
        color: "primary",
        label: "Incorrect",
        requiresIgnoreableCard: false,
        value: "incorrect",
        variant: "outlined",
    },
    {
        color: "secondary",
        label: "Correct",
        requiresIgnoreableCard: false,
        value: "correct",
        variant: "flat",
    },
    {
        color: "secondary",
        label: "Ignore",
        requiresIgnoreableCard: true,
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

async function submitGrade(grade: StudyGrade): Promise<void> {
    if (card.value === null || !revealed.value) {
        return;
    }
    if (grade === "ignore" && !card.value.can_ignore) {
        return;
    }

    pendingGrade.value = grade;

    try {
        const response = await axios.post(getUrl("study/review/"), {
            grade,
            language: selectedLanguage.value,
            record_id: card.value.record_id,
        });
        const data = response.data as StudyReviewResponse;
        card.value = data.next_card;
        revealed.value = false;
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

onMounted(async () => {
    await Promise.all([loadSummary(), loadCard(selectedLanguage.value)]);
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
  border: 1px solid rgba(91, 63, 45, 0.14);
  border-radius: 1.5rem;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.94), rgba(245, 236, 222, 0.9));
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
  border-color: rgba(139, 77, 54, 0.28);
  box-shadow: 0 18px 36px rgba(74, 49, 33, 0.08);
}

.study-language--active {
  border-color: rgba(38, 95, 85, 0.45);
  box-shadow: 0 20px 40px rgba(38, 95, 85, 0.12);
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
  color: rgba(30, 27, 24, 0.68);
  font-size: 0.95rem;
}

.study-language__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  color: #8b4d36;
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
  color: #8b4d36;
  font-size: 0.84rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.study-card-shell__counts {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  color: rgba(30, 27, 24, 0.72);
  font-size: 0.95rem;
}

.study-card {
  display: grid;
  gap: 1rem;
  padding: clamp(1.5rem, 5vw, 2.5rem);
  border: 1px solid rgba(91, 63, 45, 0.1);
  border-radius: 2rem;
  background:
    radial-gradient(circle at top right, rgba(139, 77, 54, 0.12), transparent 16rem),
    linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(247, 239, 230, 0.92));
}

.study-card__prompt {
  font-family: "Iowan Old Style", "Palatino Linotype", serif;
  font-size: clamp(2rem, 6vw, 3.4rem);
  line-height: 1.04;
}

.study-card__instruction {
  color: rgba(30, 27, 24, 0.68);
  font-size: 1rem;
}

.study-card__answer {
  min-height: 4.5rem;
  padding: 1rem 1.15rem;
  border-radius: 1.25rem;
  background: rgba(38, 95, 85, 0.11);
  color: #173d36;
  font-size: clamp(1.35rem, 4vw, 1.8rem);
  font-weight: 600;
}

.study-card__answer--hidden {
  background: rgba(91, 63, 45, 0.06);
  color: rgba(30, 27, 24, 0.45);
}

.study-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.study-status,
.study-empty {
  padding: 1.5rem;
  border: 1px dashed rgba(91, 63, 45, 0.2);
  border-radius: 1.5rem;
  background: rgba(255, 255, 255, 0.58);
}

.study-status {
  color: rgba(30, 27, 24, 0.72);
}

.study-empty__title {
  font-family: "Iowan Old Style", "Palatino Linotype", serif;
  font-size: 1.35rem;
}

.study-empty p {
  margin: 0.75rem 0 0;
  color: rgba(30, 27, 24, 0.7);
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
