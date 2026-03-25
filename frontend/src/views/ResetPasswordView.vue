<template>
  <PagePanel
    eyebrow="Authentication"
    title="Reset password"
    description="Set a new password for the account tied to this reset link."
  >
    <v-form class="form-stack" @submit.prevent="onSubmit">
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
          :disabled="password.trim().length === 0 || loading"
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
import { ref } from "vue";

import PagePanel from "../components/PagePanel.vue";
import { getUrl, rulesHelper } from "../helpers";
import { router } from "../router";
import { $toast } from "../toast";

const props = defineProps<{
  signature: string;
  timestamp: number;
  userId: number;
}>();

const rules = rulesHelper;
const password = ref("");
const showPassword = ref(false);
const loading = ref(false);

async function onSubmit(): Promise<void> {
  if (password.value.trim().length === 0) {
    return;
  }

  loading.value = true;

  try {
        await axios.post(getUrl("user/reset-password/"), {
            password: password.value,
            signature: props.signature,
            timestamp: props.timestamp,
            "user_id": props.userId,
        });
        $toast.success("Password updated.");
        await router.push("/login");
  } catch (error: unknown) {
    console.error(error);
    $toast.error("Unable to reset the password.");
  } finally {
    loading.value = false;
  }
}
</script>
