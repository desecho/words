<template>
  <PagePanel
    eyebrow="About"
    title="About Words"
    description="Words is a focused language-learning app for building vocabulary, reading saved texts, and reviewing cards with spaced repetition."
  >
    <div class="copy-block">
      <p>
        The project is built around a simple workflow: save English or French vocabulary with
        Russian translations, keep useful texts in one place, and return to the words that are
        due for review.
      </p>

      <div class="hero-grid">
        <article class="hero-card">
          <h2>What it includes</h2>
          <ul>
            <li>Add and organize vocabulary with parts of speech and optional notes.</li>
            <li>Save English and French texts and highlight words that already exist in your list.</li>
            <li>Review due cards with spaced repetition and track your progress over time.</li>
          </ul>
        </article>

        <article class="hero-card">
          <h2>How people use it</h2>
          <ul>
            <li>Capture words while reading or watching content.</li>
            <li>Study from English or French prompts while answering in Russian.</li>
          </ul>
        </article>
      </div>

      <p class="about-stack">
        The application uses Django and Django REST Framework on the backend, with Vue 3,
        TypeScript, Vuetify, and Pinia on the frontend.
      </p>

      <div class="hero-actions">
        <v-btn v-if="isLoggedIn" color="primary" to="/study" variant="flat">Start studying</v-btn>
        <v-btn v-if="isLoggedIn" to="/texts" variant="outlined">Open texts</v-btn>
        <v-btn v-if="!isLoggedIn" color="primary" to="/register" variant="flat">Create an account</v-btn>
        <v-btn v-if="!isLoggedIn" to="/login" variant="outlined">Log in</v-btn>
      </div>
    </div>
  </PagePanel>
</template>

<script lang="ts" setup>
import { computed } from "vue";

import PagePanel from "../components/PagePanel.vue";
import { useAuthStore } from "../stores/auth";

const authStore = useAuthStore();
const isLoggedIn = computed(() => authStore.user.isLoggedIn);
</script>

<style scoped>
.about-stack {
  color: var(--app-text-soft);
}
</style>
