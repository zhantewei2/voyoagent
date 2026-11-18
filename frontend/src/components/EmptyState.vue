<script setup lang="ts">
defineProps<{ icon: string; text: string }>()
</script>

<template>
  <div class="empty-state">
    <i :class="icon" />
    <span>{{ text }}</span>
  </div>
</template>
