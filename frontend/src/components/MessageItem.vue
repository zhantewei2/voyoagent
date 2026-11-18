<script setup lang="ts">
import type { ChatMessage } from '@/types/chat'
import MarkdownContent from './MarkdownContent.vue'
import ThinkingBlock from './ThinkingBlock.vue'
import ToolCallBlock from './ToolCallBlock.vue'

defineProps<{ message: ChatMessage }>()
</script>

<template>
  <div class="message-item" :class="`message-item--${message.role}`" :data-test="`message-${message.role}`">
    <div v-if="message.role === 'user'" class="bubble bubble--user">{{ message.content }}</div>
    <div v-else class="bubble bubble--assistant">
      <template v-for="(seg, index) in message.segments" :key="index">
        <ThinkingBlock v-if="seg.kind === 'thinking'" :content="seg.content" />
        <ToolCallBlock v-else-if="seg.kind === 'tool'" :segment="seg" />
        <MarkdownContent v-else :content="seg.content" />
      </template>
      <span v-if="message.segments.length === 0" class="bubble__pending">生成中…</span>
    </div>
  </div>
</template>
