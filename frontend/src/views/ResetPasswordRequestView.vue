<template>
  <PagePanel
    eyebrow="Authentication"
    title="Request a password reset"
    description="Enter your username and the backend will send a reset link."
  >
    <v-form class="form-stack" @submit.prevent="onSubmit">
      <v-text-field
        v-model="username"
        label="Username"
        :rules="[rules.required]"
      />

      <div class="action-row">
        <v-btn
          color="primary"
          :disabled="username.trim().length === 0 || loading"
          :loading="loading"
          type="submit"
          variant="flat"
        >
          Send reset link
        </v-btn>
      </div>
    </v-form>
  </PagePanel>
</template>

<script lang="ts" setup>
import axios from "axios";
import { ref } from "vue";

import PagePanel from "../components/PagePanel.vue";
import { getUrl, rulesHelper } from "../helpers";
import { $toast } from "../toast";

const rules = rulesHelper;
const username = ref("");
const loading = ref(false);

async function onSubmit(): Promise<void> {
  if (username.value.trim().length === 0) {
    return;
  }

  loading.value = true;

  try {
    await axios.post(getUrl("user/send-reset-password-link/"), {
      login: username.value.trim(),
    });
    $toast.success("Reset link sent.");
  } catch (error: unknown) {
    console.error(error);
    $toast.error("Unable to send a reset link.");
  } finally {
    loading.value = false;
  }
}
</script>
