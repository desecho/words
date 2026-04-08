<template>
  <v-app>
    <v-app-bar class="app-bar" elevation="0">
      <RouterLink aria-label="Words" class="brand" to="/">
        <img alt="Words" class="brand__logo" src="/logo.png" />
      </RouterLink>

      <v-spacer />

      <div class="nav-actions">
        <v-btn
          :aria-label="themeToggleLabel"
          :icon="themeToggleIcon"
          :title="themeToggleLabel"
          class="theme-toggle"
          variant="text"
          @click="toggleTheme"
        />
        <v-btn to="/" variant="text">Home</v-btn>
        <v-btn to="/about" variant="text">About</v-btn>
        <v-btn v-if="isLoggedIn" to="/study" variant="text">Study</v-btn>
        <v-btn v-if="isLoggedIn" to="/learn" variant="text">Learn</v-btn>
        <v-btn v-if="isLoggedIn" to="/stats" variant="text">Stats</v-btn>
        <v-btn v-if="isLoggedIn" to="/texts" variant="text">Texts</v-btn>
        <v-btn v-if="isLoggedIn" to="/words" variant="text">Words</v-btn>
        <v-btn v-if="isLoggedIn" to="/words/new" variant="text">Add word</v-btn>
        <v-btn v-if="isLoggedIn" to="/change-password" variant="text">Password</v-btn>
        <v-btn v-if="!isLoggedIn" to="/login" variant="text">Login</v-btn>
        <v-btn v-if="!isLoggedIn" color="primary" to="/register" variant="flat">Register</v-btn>
        <v-btn v-if="isLoggedIn" color="secondary" to="/logout" variant="flat">Logout</v-btn>
      </div>
    </v-app-bar>

    <v-main class="app-main">
      <v-container class="main-shell">
        <RouterView />
      </v-container>
    </v-main>

    <v-footer class="app-footer" height="auto">
      <v-container class="app-footer__container">
        <p class="app-footer__copy">
          &copy; {{ copyrightYears }}
          <a :href="`mailto:${adminEmail}`" class="app-footer__link">{{ adminEmail }}</a>.
          All rights reserved.
        </p>
      </v-container>
    </v-footer>
  </v-app>
</template>

<script lang="ts" setup>
import { computed, watch } from "vue";
import { useTheme } from "vuetify";

import {
  applyDocumentTheme,
  persistTheme,
  WORDS_DARK_THEME,
  WORDS_LIGHT_THEME,
  type WordsThemeName,
} from "./plugins/vuetify";
import { useAuthStore } from "./stores/auth";

const authStore = useAuthStore();
const theme = useTheme();
const isLoggedIn = computed(() => authStore.user.isLoggedIn);
const isDarkTheme = computed(() => theme.global.current.value.dark);
const themeToggleIcon = computed(() => (isDarkTheme.value ? "mdi-weather-sunny" : "mdi-weather-night"));
const themeToggleLabel = computed(() => (isDarkTheme.value ? "Switch to light theme" : "Switch to dark theme"));
const COPYRIGHT_START_YEAR = 2026;
const FALLBACK_ADMIN_EMAIL = "admin@example.com";
const adminEmail = import.meta.env.VITE_ADMIN_EMAIL || FALLBACK_ADMIN_EMAIL;
const currentYear = new Date().getFullYear();
const copyrightYears =
  currentYear > COPYRIGHT_START_YEAR
    ? `${COPYRIGHT_START_YEAR} - ${currentYear}`
    : `${COPYRIGHT_START_YEAR}`;

function toggleTheme(): void {
  theme.global.name.value = isDarkTheme.value ? WORDS_LIGHT_THEME : WORDS_DARK_THEME;
}

watch(
  () => theme.global.name.value,
  (themeName) => {
    const resolvedThemeName = themeName as WordsThemeName;
    applyDocumentTheme(resolvedThemeName);
    persistTheme(resolvedThemeName);
  },
  { immediate: true },
);
</script>
