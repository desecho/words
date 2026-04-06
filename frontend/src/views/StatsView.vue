<template>
  <PagePanel
    eyebrow="Stats"
    title="Learning dashboard"
    description="Track your vocabulary growth, study workload, and recent activity across English and French."
  >
    <div class="stats-layout">
      <div class="stats-toolbar">
        <div class="stats-toolbar__copy">
          <h2 class="stats-toolbar__title">Your account at a glance</h2>
          <p class="stats-toolbar__description">
            Headline totals come first, then language-specific study queues, recent activity, and collection coverage.
          </p>
        </div>
        <v-btn size="small" variant="text" :disabled="loadingStats" :loading="loadingStats" @click="loadStats">
          Refresh
        </v-btn>
      </div>

      <div v-if="loadingStats && stats === null" class="stats-state">Loading dashboard...</div>

      <div v-else-if="stats === null" class="stats-state stats-state--error">
        <div class="stats-state__title">Unable to load your stats.</div>
        <p>Try again once the backend is available.</p>
      </div>

      <template v-else>
        <section class="stats-section">
          <h2 class="stats-section__title">Overview</h2>
          <div class="stats-overview-grid">
            <article v-for="item in overviewItems" :key="item.label" class="stats-card">
              <div class="stats-card__eyebrow">{{ item.label }}</div>
              <div class="stats-card__value">{{ item.value }}</div>
              <p class="stats-card__hint">{{ item.hint }}</p>
            </article>
          </div>
        </section>

        <section class="stats-section">
          <h2 class="stats-section__title">Study by language</h2>
          <div class="stats-language-grid">
            <article v-for="language in languageCards" :key="language.code" class="stats-language-card">
              <div class="stats-language-card__header">
                <div>
                  <div class="stats-card__eyebrow">{{ language.code.toUpperCase() }}</div>
                  <h3 class="stats-language-card__title">{{ language.label }}</h3>
                </div>
                <div class="stats-language-card__rate">
                  {{ formatRate(language.success_rate) }}
                </div>
              </div>

              <div class="stats-metric-grid">
                <div class="stats-metric">
                  <span class="stats-metric__label">Due</span>
                  <span class="stats-metric__value">{{ formatCount(language.due) }}</span>
                </div>
                <div class="stats-metric">
                  <span class="stats-metric__label">Unseen</span>
                  <span class="stats-metric__value">{{ formatCount(language.unseen) }}</span>
                </div>
                <div class="stats-metric">
                  <span class="stats-metric__label">Active</span>
                  <span class="stats-metric__value">{{ formatCount(language.active) }}</span>
                </div>
                <div class="stats-metric">
                  <span class="stats-metric__label">Ignored</span>
                  <span class="stats-metric__value">{{ formatCount(language.ignored) }}</span>
                </div>
              </div>

              <div class="stats-language-card__footer">
                <span>{{ formatCount(language.reviewed_total) }} total reviews</span>
                <span>{{ formatCount(language.successful_reviews) }} successful</span>
              </div>
            </article>
          </div>
        </section>

        <section class="stats-section">
          <h2 class="stats-section__title">Recent activity</h2>
          <div class="stats-activity-grid">
            <article v-for="item in activityItems" :key="item.label" class="stats-card stats-card--compact">
              <div class="stats-card__eyebrow">{{ item.label }}</div>
              <div class="stats-card__value">{{ item.value }}</div>
              <p class="stats-card__hint">{{ item.hint }}</p>
            </article>
          </div>
        </section>

        <section class="stats-section">
          <h2 class="stats-section__title">Collection breakdown</h2>
          <div class="stats-collection-grid">
            <article class="stats-card">
              <div class="stats-card__eyebrow">Language coverage</div>
              <div class="stats-coverage-list">
                <div v-for="item in coverageItems" :key="item.label" class="stats-metric">
                  <span class="stats-metric__label">{{ item.label }}</span>
                  <span class="stats-metric__value">{{ item.value }}</span>
                </div>
              </div>
            </article>

            <article class="stats-card">
              <div class="stats-card__eyebrow">Parts of speech</div>
              <div v-if="partsOfSpeechItems.length === 0" class="stats-empty">No words yet.</div>
              <div v-else class="stats-parts-list">
                <div v-for="part in partsOfSpeechItems" :key="part.label" class="stats-parts-item">
                  <span>{{ part.label }}</span>
                  <strong>{{ formatCount(part.count) }}</strong>
                </div>
              </div>
            </article>
          </div>
        </section>
      </template>
    </div>
  </PagePanel>
</template>

<script lang="ts" setup>
import axios from "axios";
import { computed, onMounted, ref } from "vue";

import type { StatsResponse, StudyLanguage } from "../types";

import PagePanel from "../components/PagePanel.vue";
import { getUrl } from "../helpers";
import { $toast } from "../toast";

const languageOrder: StudyLanguage[] = ["en", "fr"];
const numberFormatter = new Intl.NumberFormat();

const loadingStats = ref(false);
const stats = ref<StatsResponse | null>(null);

function formatCount(value: number): string {
  return numberFormatter.format(value);
}

function formatRate(value: number): string {
  return `${value.toFixed(Number.isInteger(value) ? 0 : 1)}%`;
}

const overviewItems = computed(() => {
  if (stats.value === null) {
    return [];
  }

  return [
    {
      hint: "Words saved in your account",
      label: "Words",
      value: formatCount(stats.value.overview.words_total),
    },
    {
      hint: "Texts saved for reading and matching",
      label: "Texts",
      value: formatCount(stats.value.overview.texts_total),
    },
    {
      hint: "Flashcard records available to study",
      label: "Records",
      value: formatCount(stats.value.overview.records_total),
    },
    {
      hint: "All recorded review attempts",
      label: "Reviews",
      value: formatCount(stats.value.overview.reviews_total),
    },
    {
      hint: `${formatCount(stats.value.overview.reviews_successful)} successful reviews`,
      label: "Success rate",
      value: formatRate(stats.value.overview.review_success_rate),
    },
  ];
});

const languageCards = computed(() => {
  if (stats.value === null) {
    return [];
  }

  const studyStats = stats.value.study;

  return languageOrder.map((code) => ({
    code,
    ...studyStats[code],
  }));
});

const activityItems = computed(() => {
  if (stats.value === null) {
    return [];
  }

  return [
    {
      hint: "Words added during the last 7 days",
      label: "Words added (7d)",
      value: formatCount(stats.value.activity.recent_words_added_7d),
    },
    {
      hint: "Texts added during the last 7 days",
      label: "Texts added (7d)",
      value: formatCount(stats.value.activity.recent_texts_added_7d),
    },
    {
      hint: "Cards touched in the last 7 days",
      label: "Cards reviewed (7d)",
      value: formatCount(stats.value.activity.recent_reviews_7d),
    },
  ];
});

const coverageItems = computed(() => {
  if (stats.value === null) {
    return [];
  }

  return [
    {
      label: "With English",
      value: formatCount(stats.value.collection.language_coverage.with_english),
    },
    {
      label: "With French",
      value: formatCount(stats.value.collection.language_coverage.with_french),
    },
    {
      label: "With both",
      value: formatCount(stats.value.collection.language_coverage.with_both),
    },
  ];
});

const partsOfSpeechItems = computed(() => stats.value?.collection.parts_of_speech ?? []);

async function loadStats(): Promise<void> {
  loadingStats.value = true;

  try {
    const response = await axios.get(getUrl("stats/summary/"));
    stats.value = response.data as StatsResponse;
  } catch (error: unknown) {
    console.error(error);
    $toast.error("Unable to load stats.");
  } finally {
    loadingStats.value = false;
  }
}

onMounted(async () => {
  await loadStats();
});
</script>

<style scoped>
.stats-layout {
  display: grid;
  gap: 1.5rem;
}

.stats-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.stats-toolbar__copy {
  max-width: 34rem;
}

.stats-toolbar__title {
  margin: 0;
  font-family: "Iowan Old Style", "Palatino Linotype", serif;
  font-size: 1.5rem;
}

.stats-toolbar__description {
  margin: 0.5rem 0 0;
  color: var(--app-text-muted);
  line-height: 1.6;
}

.stats-section {
  display: grid;
  gap: 1rem;
}

.stats-section__title {
  margin: 0;
  font-family: "Iowan Old Style", "Palatino Linotype", serif;
  font-size: 1.35rem;
}

.stats-overview-grid,
.stats-activity-grid,
.stats-collection-grid,
.stats-language-grid {
  display: grid;
  gap: 1rem;
}

.stats-overview-grid {
  grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
}

.stats-activity-grid,
.stats-collection-grid,
.stats-language-grid {
  grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
}

.stats-card,
.stats-language-card,
.stats-state {
  padding: 1.25rem;
  border: 1px solid var(--card-border);
  background: var(--card-gradient);
  box-shadow: var(--shadow-card-hover);
}

.stats-card__eyebrow {
  color: var(--app-text-soft);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.stats-card__value {
  margin-top: 0.6rem;
  font-family: "Iowan Old Style", "Palatino Linotype", serif;
  font-size: clamp(1.8rem, 3vw, 2.6rem);
  line-height: 1;
}

.stats-card__hint {
  margin: 0.75rem 0 0;
  color: var(--app-text-muted);
  line-height: 1.55;
}

.stats-card--compact .stats-card__value {
  font-size: clamp(1.6rem, 2.8vw, 2.2rem);
}

.stats-language-card {
  display: grid;
  gap: 1rem;
  background: var(--study-card-bg);
}

.stats-language-card__header,
.stats-language-card__footer {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.stats-language-card__title {
  margin: 0.35rem 0 0;
  font-family: "Iowan Old Style", "Palatino Linotype", serif;
  font-size: 1.4rem;
}

.stats-language-card__rate {
  font-size: 1rem;
  font-weight: 700;
  color: rgb(var(--v-theme-secondary));
}

.stats-metric-grid,
.stats-coverage-list {
  display: grid;
  gap: 0.75rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.stats-metric {
  display: grid;
  gap: 0.2rem;
  padding: 0.8rem 0.9rem;
  background: var(--subtle-bg);
}

.stats-metric__label {
  color: var(--app-text-soft);
  font-size: 0.85rem;
}

.stats-metric__value {
  font-size: 1.15rem;
  font-weight: 700;
}

.stats-language-card__footer {
  color: var(--app-text-muted);
  font-size: 0.95rem;
}

.stats-parts-list {
  display: grid;
  gap: 0.7rem;
  margin-top: 0.9rem;
}

.stats-parts-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.75rem 0.9rem;
  border: 1px solid var(--card-border);
  background: var(--card-bg);
}

.stats-empty {
  margin-top: 0.9rem;
  color: var(--app-text-muted);
}

.stats-state {
  background: var(--empty-bg);
}

.stats-state--error {
  border-color: rgba(var(--v-theme-error), 0.28);
}

.stats-state__title {
  font-family: "Iowan Old Style", "Palatino Linotype", serif;
  font-size: 1.35rem;
}

.stats-state p {
  margin: 0.5rem 0 0;
  color: var(--app-text-muted);
}

@media (max-width: 720px) {
  .stats-language-card__header,
  .stats-language-card__footer,
  .stats-toolbar {
    align-items: stretch;
    flex-direction: column;
  }

  .stats-metric-grid,
  .stats-coverage-list {
    grid-template-columns: 1fr;
  }
}
</style>
