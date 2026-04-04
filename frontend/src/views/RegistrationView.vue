<template>
  <PagePanel
    eyebrow="Authentication"
    title="Create an account"
  >
    <v-form class="form-stack" @submit.prevent="onSubmit">
      <v-text-field
        v-model="username"
        label="Username"
        :rules="[rules.required]"
      />
      <v-text-field
        v-model="email"
        label="Email"
        :rules="[rules.required, rules.email]"
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
          Register
        </v-btn>
      </div>
    </v-form>
  </PagePanel>
</template>

<script lang="ts" setup>
import axios from "axios";
import { computed, ref } from "vue";
import { useRouter } from "vue-router";

import PagePanel from "../components/PagePanel.vue";
import { getUrl, rulesHelper } from "../helpers";
import { $toast } from "../toast";

const router = useRouter();
const rules = rulesHelper;

const username = ref("");
const email = ref("");
const password = ref("");
const showPassword = ref(false);
const loading = ref(false);

const canSubmit = computed(() => {
  return (
    username.value.trim().length > 0 &&
    password.value.trim().length > 0 &&
    typeof rules.email(email.value) === "boolean"
  );
});

function showFieldErrors(errorData: Record<string, unknown>): void {
  for (const value of Object.values(errorData)) {
    if (Array.isArray(value)) {
      value.forEach((message) => {
        if (typeof message === "string") {
          $toast.error(message);
        }
      });
    }
  }
}

async function onSubmit(): Promise<void> {
  if (!canSubmit.value) {
    return;
  }

  loading.value = true;

  try {
    const availabilityResponse = await axios.post(
      getUrl("user/check-email-availability/"),
      { email: email.value.trim() },
    );

    if (availabilityResponse.data !== true) {
      $toast.error("A user with this email is already registered.");
      return;
    }

    await axios.post(getUrl("user/register/"), {
      email: email.value.trim(),
      password: password.value,
      username: username.value.trim(),
    });

    $toast.success("Check your email for the verification link.");
    await router.push("/register/success");
  } catch (error: unknown) {
    console.error(error);

    if (
      typeof error === "object" &&
      error !== null &&
      "response" in error &&
      typeof error.response === "object" &&
      error.response !== null &&
      "data" in error.response &&
      typeof error.response.data === "object" &&
      error.response.data !== null
    ) {
      showFieldErrors(error.response.data as Record<string, unknown>);
      return;
    }

    $toast.error("Registration failed.");
  } finally {
    loading.value = false;
  }
}
</script>
