<template>
  <PagePanel
    eyebrow="Account"
    title="Profile settings"
    description="This is a minimal authenticated page kept in the template so the frontend auth flow has a real private route to land on."
  >
    <v-form class="form-stack" @submit.prevent="onSubmit">
      <v-text-field
        :model-value="username"
        label="Username"
        readonly
      />
      <v-text-field
        v-model="email"
        label="Email"
        :rules="[rules.required, rules.email]"
      />

      <div class="action-row">
        <v-btn
          color="primary"
          :disabled="!canSubmit || loading"
          :loading="loading"
          type="submit"
          variant="flat"
        >
          Save changes
        </v-btn>
      </div>
    </v-form>
  </PagePanel>
</template>

<script lang="ts" setup>
import axios from "axios";
import { computed, onMounted, ref } from "vue";

import type { UserPreferences } from "../types";

import PagePanel from "../components/PagePanel.vue";
import { getUrl, rulesHelper } from "../helpers";
import { $toast } from "../toast";

const rules = rulesHelper;

const username = ref("");
const email = ref("");
const loading = ref(false);

const canSubmit = computed(() => typeof rules.email(email.value) === "boolean");

async function loadPreferences(): Promise<void> {
  const response = await axios.get(getUrl("user/preferences/"));
  const data = response.data as UserPreferences;
  email.value = data.email;
  username.value = data.username;
}

async function onSubmit(): Promise<void> {
  if (!canSubmit.value) {
    return;
  }

  loading.value = true;

    try {
        const response = await axios.put(getUrl("user/preferences/"), {
            email: email.value.trim(),
        });
        const data = response.data as UserPreferences;
        // eslint-disable-next-line require-atomic-updates
        email.value = data.email;
        $toast.success("Profile updated.");
    } catch (error: unknown) {
    console.error(error);
    $toast.error("Unable to update the profile.");
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  try {
    await loadPreferences();
  } catch (error: unknown) {
    console.error(error);
    $toast.error("Unable to load the profile.");
  }
});
</script>
