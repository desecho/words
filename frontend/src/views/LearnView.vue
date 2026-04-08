<template>
  <PagePanel
    eyebrow="Learn"
    title="Review the words you missed"
    description="Choose a study language and scan the words whose latest review result was incorrect."
  >
    <div class="learn-layout">
      <div class="learn-language-grid">
        <button
          v-for="option in languageOptions"
          :key="option.code"
          class="learn-language"
          :class="{ 'learn-language--active': selectedLanguage === option.code }"
          type="button"
          @click="selectedLanguage = option.code"
        >
          <div class="learn-language__title">{{ option.title }}</div>
          <div class="learn-language__cue">{{ option.cue }}</div>
        </button>
      </div>

      <section class="learn-section">
        <div class="learn-section__header">
          <div>
            <h2 class="learn-section__title">
              {{ selectedLanguageOption.title }} to Russian
            </h2>
            <p class="learn-section__description">
              Sorted by the most recently missed words.
            </p>
          </div>

          <div class="learn-section__actions">
            <span class="learn-section__count">{{ resultsLabel }}</span>
            <v-btn
              size="small"
              variant="text"
              :disabled="loadingWords"
              :loading="loadingWords"
              @click="reloadCurrentLanguage"
            >
              Refresh
            </v-btn>
          </div>
        </div>

        <div v-if="loadingWords && incorrectWords.length === 0" class="learn-state">
          Loading incorrect words...
        </div>
        <div
          v-else-if="loadFailed && incorrectWords.length === 0"
          class="learn-state learn-state--error"
        >
          <div class="learn-state__title">Unable to load your Learn list.</div>
          <p>Try again once the backend is available.</p>
        </div>
        <div v-else-if="incorrectWords.length === 0" class="learn-state">
          <div class="learn-state__title">No incorrect words right now.</div>
          <p>
            {{ selectedLanguageOption.title }} words will appear here after they are
            graded as incorrect in Study.
          </p>
        </div>
        <div v-else class="learn-table-shell">
          <table class="learn-table">
            <thead>
              <tr>
                <th scope="col">{{ selectedLanguageOption.title }}</th>
                <th scope="col">Russian</th>
                <th scope="col">Part of speech</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="word in incorrectWords"
                :key="`${word.language}-${word.record_id}`"
              >
                <td class="learn-table__prompt">{{ word.prompt }}</td>
                <td>{{ word.ru }}</td>
                <td>{{ word.part_of_speech_label }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  </PagePanel>
</template>

<script lang="ts" setup>
import axios from "axios";
import { computed, onMounted, ref, watch } from "vue";

import type { LearnListResponse, LearnWordItem, StudyLanguage } from "../types";

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

const selectedLanguage = ref<StudyLanguage>("en");
const incorrectWords = ref<LearnWordItem[]>([]);
const loadingWords = ref(false);
const loadFailed = ref(false);

const selectedLanguageOption = computed(
  () =>
    languageOptions.find((option) => option.code === selectedLanguage.value) ??
    languageOptions[0],
);

const resultsLabel = computed(() => {
  const count = incorrectWords.value.length;
  return count === 1 ? "1 incorrect word" : `${count} incorrect words`;
});

async function loadIncorrectWords(language: StudyLanguage): Promise<void> {
  loadingWords.value = true;
  loadFailed.value = false;
  const requestedLanguage = language;

  try {
    const response = await axios.get(getUrl("study/incorrect-words/"), {
      params: { language },
    });
    const data = response.data as LearnListResponse;

    if (selectedLanguage.value === requestedLanguage) {
      incorrectWords.value = data.words;
    }
  } catch (error: unknown) {
    console.error(error);

    if (selectedLanguage.value === requestedLanguage) {
      incorrectWords.value = [];
      loadFailed.value = true;
    }

    $toast.error("Unable to load incorrect words.");
  } finally {
    if (selectedLanguage.value === requestedLanguage) {
      loadingWords.value = false;
    }
  }
}

async function reloadCurrentLanguage(): Promise<void> {
  await loadIncorrectWords(selectedLanguage.value);
}

watch(selectedLanguage, async (language, previousLanguage) => {
  if (language === previousLanguage) {
    return;
  }

  await loadIncorrectWords(language);
});

onMounted(async () => {
  await loadIncorrectWords(selectedLanguage.value);
});
</script>

<style scoped>
.learn-layout {
  display: grid;
  gap: 1.5rem;
}

.learn-language-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.learn-language {
  display: grid;
  gap: 0.35rem;
  padding: 1rem 1.15rem;
  border: 1px solid var(--card-border);
  border-radius: 1.35rem;
  background: var(--card-gradient);
  cursor: pointer;
  font: inherit;
  text-align: left;
  transition:
    transform 140ms ease,
    border-color 140ms ease,
    box-shadow 140ms ease;
}

.learn-language:hover {
  transform: translateY(-2px);
  border-color: rgba(var(--v-theme-primary), 0.28);
  box-shadow: var(--shadow-card-hover);
}

.learn-language--active {
  border-color: rgba(var(--v-theme-secondary), 0.45);
  box-shadow: var(--shadow-card-active);
}

.learn-language__title {
  font-family: "Iowan Old Style", "Palatino Linotype", serif;
  font-size: 1.35rem;
  line-height: 1.1;
}

.learn-language__cue {
  color: var(--app-text-soft);
  font-size: 0.95rem;
}

.learn-section {
  display: grid;
  gap: 1rem;
}

.learn-section__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.learn-section__title {
  margin: 0;
  font-family: "Iowan Old Style", "Palatino Linotype", serif;
  font-size: 1.5rem;
}

.learn-section__description {
  margin: 0.45rem 0 0;
  color: var(--app-text-muted);
  line-height: 1.6;
}

.learn-section__actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.learn-section__count {
  color: rgb(var(--v-theme-primary));
  font-size: 0.92rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.learn-state,
.learn-table-shell {
  padding: 1.25rem;
  border: 1px solid var(--card-border);
  border-radius: 1.5rem;
  background: var(--card-bg);
}

.learn-state--error {
  background: var(--empty-bg);
}

.learn-state__title {
  font-family: "Iowan Old Style", "Palatino Linotype", serif;
  font-size: 1.35rem;
}

.learn-state p {
  margin: 0.75rem 0 0;
  color: var(--app-text-muted);
  line-height: 1.6;
}

.learn-table-shell {
  overflow-x: auto;
}

.learn-table {
  min-width: 32rem;
  width: 100%;
  border-collapse: collapse;
}

.learn-table th,
.learn-table td {
  padding: 0.95rem 1rem;
  border-bottom: 1px solid var(--card-border);
  text-align: left;
}

.learn-table th {
  color: rgb(var(--v-theme-primary));
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.learn-table tbody tr:last-child td {
  border-bottom: 0;
}

.learn-table tbody tr:hover {
  background: var(--subtle-bg);
}

.learn-table__prompt {
  font-family: "Iowan Old Style", "Palatino Linotype", serif;
  font-size: 1.15rem;
}

@media (max-width: 720px) {
  .learn-language-grid {
    grid-template-columns: 1fr;
  }
}
</style>
