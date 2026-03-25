<template>
  <PagePanel
    eyebrow="Starter"
    title="A blank Django and Vue workspace for building words."
    description="The project keeps the harness from shows, preserves JWT-based frontend auth, and removes the old TV-show domain code."
  >
    <div class="hero-grid">
      <v-card class="hero-card" elevation="0">
        <h2>What stays</h2>
        <ul>
          <li>Django backend with JWT auth and registration flow</li>
          <li>Vue 3 + Vite frontend with Axios token refresh</li>
          <li>Makefile, Docker, deployment files, and CI harness</li>
        </ul>
      </v-card>

      <v-card class="hero-card" elevation="0">
        <h2>What changed</h2>
        <ul>
          <li>No Celery worker or task queue wiring</li>
          <li>No show, recommendation, provider, or API integration code</li>
          <li>A cleaner starter surface for your next feature set</li>
        </ul>
      </v-card>
    </div>

    <div class="hero-actions">
      <v-btn color="primary" size="large" to="/register" variant="flat">Create an account</v-btn>
      <v-btn size="large" to="/login" variant="outlined">Sign in</v-btn>
    </div>
  </PagePanel>
</template>

<script lang="ts" setup>
import PagePanel from "../components/PagePanel.vue";
</script>
