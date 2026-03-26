<template>
  <v-app>
    <v-app-bar class="app-bar" elevation="0">
      <RouterLink class="brand" to="/">
        <span class="brand__mark">W</span>
        <span class="brand__text">words</span>
      </RouterLink>

      <v-spacer />

      <div class="nav-actions">
        <v-btn to="/" variant="text">Home</v-btn>
        <v-btn v-if="isLoggedIn" to="/study" variant="text">Study</v-btn>
        <v-btn v-if="isLoggedIn" to="/texts" variant="text">Texts</v-btn>
        <v-btn v-if="isLoggedIn" to="/words/new" variant="text">Add word</v-btn>
        <v-btn v-if="isLoggedIn" to="/change-password" variant="text">Password</v-btn>
        <v-btn v-if="!isLoggedIn" to="/login" variant="text">Login</v-btn>
        <v-btn v-if="!isLoggedIn" color="primary" to="/register" variant="flat">Register</v-btn>
        <v-btn v-if="isLoggedIn" color="secondary" to="/logout" variant="flat">Logout</v-btn>
      </div>
    </v-app-bar>

    <v-main>
      <v-container class="main-shell">
        <RouterView />
      </v-container>
    </v-main>
  </v-app>
</template>

<script lang="ts" setup>
import { computed } from "vue";

import { useAuthStore } from "./stores/auth";

const authStore = useAuthStore();
const isLoggedIn = computed(() => authStore.user.isLoggedIn);
</script>
