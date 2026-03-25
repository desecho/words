<template>
  <PagePanel
    eyebrow="Authentication"
    title="Check your email"
    description="The starter is configured to send registration verification and reset-password links through Django REST Registration."
  >
    <div class="copy-block">
      <p>
        If email delivery is configured, you should receive a verification link shortly.
        In development, the default backend prints the email to the server console.
      </p>
      <v-btn color="primary" to="/login" variant="flat">Back to login</v-btn>
    </div>
  </PagePanel>
</template>

<script lang="ts" setup>
import PagePanel from "../components/PagePanel.vue";
</script>
