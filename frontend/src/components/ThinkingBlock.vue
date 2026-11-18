<script setup lang="ts">
defineProps<{ content: string }>()
</script>

<template>
  <n-collapse class="thinking-block" data-test="thinking-block" arrow-placement="left">
    <n-collapse-item name="thinking">
      <template #header>
        <span class="thinking-block__title">思考过程</span>
      </template>
      <div class="thinking-block__content">{{ content }}</div>
    </n-collapse-item>
  </n-collapse>
</template>
