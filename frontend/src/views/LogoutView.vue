<template>
  <PagePanel
    eyebrow="Authentication"
    title="Signing you out"
    description="Your local auth state is being cleared."
  />
</template>

<script lang="ts" setup>
import { onMounted } from "vue";

import PagePanel from "../components/PagePanel.vue";
import { useAuthStore } from "../stores/auth";

onMounted(() => {
  useAuthStore().logout();
});
</script>
