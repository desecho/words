<template>
  <PagePanel
    eyebrow="Account"
    title="Change password"
    description="This page uses the authenticated password-change endpoint from Django REST Registration."
  >
    <v-form class="form-stack" @submit.prevent="onSubmit">
      <v-text-field
        v-model="oldPassword"
        label="Current password"
        :append-inner-icon="showOldPassword ? 'mdi-eye-off' : 'mdi-eye'"
        :type="showOldPassword ? 'text' : 'password'"
        :rules="[rules.required]"
        @click:append-inner="showOldPassword = !showOldPassword"
      />
      <v-text-field
        v-model="password"
        label="New password"
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
          Save password
        </v-btn>
      </div>
    </v-form>
  </PagePanel>
</template>

<script lang="ts" setup>
import axios from "axios";
import { computed, ref } from "vue";

import PagePanel from "../components/PagePanel.vue";
import { getUrl, rulesHelper } from "../helpers";
import { router } from "../router";
import { $toast } from "../toast";

const rules = rulesHelper;

const oldPassword = ref("");
const password = ref("");
const showOldPassword = ref(false);
const showPassword = ref(false);
const loading = ref(false);

const canSubmit = computed(() => {
  return oldPassword.value.trim().length > 0 && password.value.trim().length > 0;
});

async function onSubmit(): Promise<void> {
  if (!canSubmit.value) {
    return;
  }

  loading.value = true;

    try {
        await axios.post(getUrl("user/change-password/"), {
            password: password.value,
            "old_password": oldPassword.value,
        });
        $toast.success("Password changed.");
        await router.push("/preferences");
  } catch (error: unknown) {
    console.error(error);
    $toast.error("Unable to change the password.");
  } finally {
    loading.value = false;
  }
}
</script>
