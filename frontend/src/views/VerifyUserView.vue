<template>
  <PagePanel
    eyebrow="Authentication"
    title="Verifying your account"
    :description="message"
  >
    <div class="copy-block">
      <v-progress-circular
        v-if="loading"
        color="primary"
        indeterminate
      />
      <v-btn v-else color="primary" to="/login" variant="flat">Go to login</v-btn>
    </div>
  </PagePanel>
</template>

<script lang="ts" setup>
import axios from "axios";
import { onMounted, ref } from "vue";

import PagePanel from "../components/PagePanel.vue";
import { getUrl } from "../helpers";
import { router } from "../router";
import { $toast } from "../toast";

const props = defineProps<{
  signature: string;
  timestamp: number;
  userId: number;
}>();

const loading = ref(true);
const message = ref("Please wait while the verification link is confirmed.");

onMounted(async () => {
    try {
        await axios.post(getUrl("user/verify-registration/"), {
            signature: props.signature,
            timestamp: props.timestamp,
            "user_id": props.userId,
        });
        $toast.success("Registration verified.");
    message.value = "Your account is active. You can sign in now.";
    await router.push("/login");
  } catch (error: unknown) {
    console.error(error);
    message.value = "The verification link is invalid or expired.";
    $toast.error("Unable to verify the account.");
  } finally {
    loading.value = false;
  }
});
</script>
