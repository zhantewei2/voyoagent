<script setup lang="ts">
defineProps<{ label: string; desc?: string }>()
</script>

<template>
  <div class="option-label">
    <span class="option-label__name">{{ label }}</span>
    <span v-if="desc" class="option-label__desc">{{ desc }}</span>
  </div>
</template>
