<template>
  <PagePanel
    eyebrow="Authentication"
    title="Sign in"
    description="Use the JWT auth flow preserved from the original harness."
  >
    <v-form class="form-stack" @submit.prevent="onSubmit">
      <v-text-field
        v-model="username"
        label="Username"
        :rules="[rules.required]"
      />
      <v-text-field
        v-model="password"
        label="Password"
        :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
        :type="showPassword ? 'text' : 'password'"
        :rules="[rules.required]"
        @click:append-inner="showPassword = !showPassword"
      />

      <div class="action-row">
        <v-btn
          color="primary"
          :disabled="!canSubmit || loading"
          :loading="loading"
          type="submit"
          variant="flat"
        >
          Login
        </v-btn>
        <v-btn to="/reset-password-request" variant="text">Forgot password?</v-btn>
      </div>
    </v-form>
  </PagePanel>
</template>

<script lang="ts" setup>
import { computed, ref } from "vue";

import PagePanel from "../components/PagePanel.vue";
import { rulesHelper } from "../helpers";
import { useAuthStore } from "../stores/auth";
import { $toast } from "../toast";

const authStore = useAuthStore();
const rules = rulesHelper;

const username = ref("");
const password = ref("");
const showPassword = ref(false);
const loading = ref(false);

const canSubmit = computed(
  () => username.value.trim().length > 0 && password.value.trim().length > 0,
);

async function onSubmit(): Promise<void> {
  if (!canSubmit.value) {
    return;
  }

  loading.value = true;

  try {
    await authStore.login(username.value.trim(), password.value);
    $toast.success("Welcome back.");
  } catch (error: unknown) {
    console.error(error);
    $toast.error("Unable to sign in.");
  } finally {
    loading.value = false;
  }
}
</script>
