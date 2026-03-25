<template>
  <PagePanel
    eyebrow="Words"
    title="Add a new word"
    description="Create a new word from the UI. A matching record for your account will be created automatically."
  >
    <v-form class="form-stack" @submit.prevent="onSubmit">
      <v-text-field
        v-model="ru"
        label="Russian"
        :error-messages="fieldErrors.ru"
      />
      <v-text-field
        v-model="en"
        label="English"
        :error-messages="fieldErrors.en"
      />
      <v-text-field
        v-model="fr"
        label="French"
        :error-messages="fieldErrors.fr"
      />
      <v-select
        v-model="partOfSpeechId"
        :disabled="loadingOptions"
        :error-messages="fieldErrors.part_of_speech_id"
        :items="partOfSpeechItems"
        item-title="label"
        item-value="id"
        label="Part of speech"
      />
      <v-text-field
        v-model="comment"
        label="Comment"
        :error-messages="fieldErrors.comment"
      />

      <div v-if="fieldErrors.non_field_errors.length > 0" class="form-error">
        {{ fieldErrors.non_field_errors[0] }}
      </div>

      <div class="action-row">
        <v-btn
          color="primary"
          :disabled="loading"
          :loading="loading"
          type="submit"
          variant="flat"
        >
          Add word
        </v-btn>
      </div>
    </v-form>
  </PagePanel>
</template>

<script lang="ts" setup>
import axios from "axios";
import { computed, onMounted, ref } from "vue";

import type {
    CreateWordRequest,
    CreateWordResponse,
    PartOfSpeechListResponse,
    PartOfSpeechOption,
} from "../types";

import PagePanel from "../components/PagePanel.vue";
import { getUrl } from "../helpers";
import { router } from "../router";
import { $toast } from "../toast";

type WordFormErrors = {
    comment: string[];
    en: string[];
    fr: string[];
    non_field_errors: string[];
    part_of_speech_id: string[];
    ru: string[];
};

const comment = ref("");
const en = ref("");
const fr = ref("");
const loading = ref(false);
const loadingOptions = ref(false);
const partOfSpeechId = ref<number | null>(null);
const partOfSpeechOptions = ref<PartOfSpeechOption[]>([]);
const ru = ref("");
const fieldErrors = ref<WordFormErrors>({
    comment: [],
    en: [],
    fr: [],
    non_field_errors: [],
    part_of_speech_id: [],
    ru: [],
});

const partOfSpeechItems = computed(() =>
    partOfSpeechOptions.value.map((option) => ({
        ...option,
        label: `${option.name} (${option.abbreviation})`,
    })),
);

function resetFieldErrors(): void {
    fieldErrors.value = {
        comment: [],
        en: [],
        fr: [],
        non_field_errors: [],
        part_of_speech_id: [],
        ru: [],
    };
}

function validateForm(): boolean {
    resetFieldErrors();

    if (ru.value.trim().length === 0) {
        fieldErrors.value.ru = ["Russian is required."];
    }
    if (partOfSpeechId.value === null) {
        fieldErrors.value.part_of_speech_id = ["Part of speech is required."];
    }
    if (en.value.trim().length === 0 && fr.value.trim().length === 0) {
        fieldErrors.value.non_field_errors = [
            "Provide at least one of English or French.",
        ];
    }

    return Object.values(fieldErrors.value).every((messages) => messages.length === 0);
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

function applyServerErrors(errorData: Record<string, unknown>): void {
    resetFieldErrors();

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

async function onSubmit(): Promise<void> {
    if (!validateForm()) {
        return;
    }

    loading.value = true;

    try {
        const payload: CreateWordRequest = {
            comment: comment.value.trim(),
            en: en.value.trim(),
            fr: fr.value.trim(),
            part_of_speech_id: partOfSpeechId.value,
            ru: ru.value.trim(),
        };

        await axios.post<CreateWordResponse>(getUrl("words/"), payload);
        $toast.success("Word added.");
        await router.push("/study");
    } catch (error: unknown) {
        console.error(error);
        if (axios.isAxiosError(error) && error.response?.data) {
            applyServerErrors(error.response.data as Record<string, unknown>);
        } else {
            $toast.error("Unable to add the word.");
        }
    } finally {
        loading.value = false;
    }
}

onMounted(async () => {
    await loadPartOfSpeechOptions();
});
</script>

<style scoped>
.form-error {
  padding: 0.9rem 1rem;
  border-radius: 1rem;
  background: rgba(139, 77, 54, 0.12);
  color: #8b4d36;
  line-height: 1.5;
}
</style>
