<template>
  <PagePanel
    eyebrow="Texts"
    :title="text?.name ?? 'Text detail'"
    description="Highlighted words come from your saved records for this language. Articles, contractions, and number words are marked automatically."
  >
    <div class="text-detail-layout">
      <div class="action-row">
        <v-btn to="/texts" variant="text">Back to texts</v-btn>
      </div>

      <div v-if="loading" class="text-detail-empty">
        Loading text...
      </div>

      <template v-else-if="text">
        <div class="text-detail-meta">
          <span>{{ languageLabelByCode[text.language] }}</span>
          <span>{{ formatDate(text.date_added) }}</span>
        </div>

        <div class="text-legend">
          <span class="text-legend__item">
            <span class="text-token text-token--record">word</span>
            Saved word
          </span>
          <span class="text-legend__item">
            <span class="text-token text-token--automatic">auto</span>
            Automatic language match
          </span>
        </div>

        <div class="text-content" aria-label="Processed text">
          <template v-for="(segment, index) in segments" :key="index">
            <span
              v-if="segment.type === 'match'"
              class="text-token"
              :class="segment.match_kind === 'record' ? 'text-token--record' : 'text-token--automatic'"
              :title="segment.match_kind === 'record' ? 'Saved word' : automaticMatchLabel(segment.match_kind)"
            >
              {{ segment.value }}
            </span>
            <span v-else>{{ segment.value }}</span>
          </template>
        </div>
      </template>

      <div v-else class="text-detail-empty">
        Unable to load this text.
      </div>
    </div>
  </PagePanel>
</template>

<script lang="ts" setup>
import axios from "axios";
import { onMounted, ref } from "vue";

import type {
    StudyLanguage,
    TextDetailResponse,
    TextItem,
    TextMatchSegment,
    TextSegment,
} from "../types";

import PagePanel from "../components/PagePanel.vue";
import { getUrl } from "../helpers";
import { $toast } from "../toast";

const props = defineProps<{
    id: string | string[];
}>();

const languageLabelByCode: Record<StudyLanguage, string> = {
    en: "English",
    fr: "French",
};

const loading = ref(false);
const segments = ref<TextSegment[]>([]);
const text = ref<TextItem | null>(null);

function automaticMatchLabel(matchKind: TextMatchSegment["match_kind"]): string {
    if (matchKind === "article") {
        return "Article";
    }
    if (matchKind === "contraction") {
        return "Contraction";
    }
    if (matchKind === "number_word") {
        return "Number word";
    }
    return "Saved word";
}

function formatDate(value: string): string {
    return new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
    }).format(new Date(value));
}

function getTextId(): number {
    const rawId = Array.isArray(props.id) ? props.id[0] : props.id;
    return Number(rawId);
}

async function loadText(): Promise<void> {
    loading.value = true;

    try {
        const response = await axios.get(getUrl(`texts/${getTextId()}/`));
        const data = response.data as TextDetailResponse;
        segments.value = data.segments;
        text.value = data.text;
    } catch (error: unknown) {
        console.error(error);
        text.value = null;
        segments.value = [];
        $toast.error("Unable to load the text.");
    } finally {
        loading.value = false;
    }
}

onMounted(async () => {
    await loadText();
});
</script>

<style scoped>
.text-detail-layout {
  display: grid;
  gap: 1.25rem;
}

.text-detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  color: var(--app-text-soft);
  font-size: 0.95rem;
}

.text-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 0.9rem;
}

.text-legend__item {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  color: var(--app-text-muted);
  font-size: 0.94rem;
}

.text-content {
  padding: 1.25rem;
  border: 1px solid var(--card-border);
  background: var(--card-bg);
  color: var(--app-text);
  font-size: 1.05rem;
  line-height: 1.9;
  white-space: pre-wrap;
  word-break: break-word;
}

.text-token {
  padding: 0.08rem 0.2rem;
  border-radius: 0.35rem;
}

.text-token--record {
  background: rgba(var(--v-theme-primary), 0.18);
  box-shadow: inset 0 0 0 1px rgba(var(--v-theme-primary), 0.16);
}

.text-token--automatic {
  background: rgba(var(--v-theme-warning), 0.18);
  box-shadow: inset 0 0 0 1px rgba(var(--v-theme-warning), 0.2);
}

.text-detail-empty {
  padding: 1rem 1.1rem;
  border: 1px dashed var(--empty-border);
  background: var(--empty-bg);
  color: var(--app-text-soft);
}
</style>
