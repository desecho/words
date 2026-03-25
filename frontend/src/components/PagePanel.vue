<template>
  <v-sheet class="page-panel" elevation="0">
    <div class="page-panel__eyebrow">{{ eyebrow }}</div>
    <h1 class="page-panel__title">{{ title }}</h1>
    <p v-if="description" class="page-panel__description">{{ description }}</p>
    <div class="page-panel__body">
      <slot />
    </div>
  </v-sheet>
</template>

<script lang="ts" setup>
defineProps<{
  description?: string;
  eyebrow: string;
  title: string;
}>();
</script>
