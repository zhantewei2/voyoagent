<script setup lang="ts">
import type { ComponentPublicInstance } from 'vue'
import { nextTick, onMounted, reactive, watch } from 'vue'
import { state } from '@/stores/chat'
import EmptyState from './EmptyState.vue'
import MessageItem from './MessageItem.vue'

const local = reactive({ el: null as HTMLElement | null })

function setListEl(node: Element | ComponentPublicInstance | null): void {
  local.el = node instanceof HTMLElement ? node : null
}

async function scrollToBottom(): Promise<void> {
  await nextTick()
  const el = local.el
  if (el) el.scrollTop = el.scrollHeight
}

//轻量滚动触发：消息数 + 末条助手片段数 + 末片段内容长度，避免整体序列化
function scrollTick(): string {
  const last = state.messages[state.messages.length - 1]
  const segs = last && last.role === 'assistant' ? last.segments : []
  const tail = segs[segs.length - 1]
  const tailLen = tail?.kind === 'tool' ? tail.result.length : tail ? tail.content.length : 0
  return `${state.messages.length}:${segs.length}:${tailLen}`
}

// 消息结构或流式增量变化时滚动到底部
watch(scrollTick, () => void scrollToBottom())

onMounted(() => void scrollToBottom())
</script>

<template>
  <main class="chat-messages" data-test="message-list" :ref="setListEl">
    <EmptyState v-if="state.messages.length === 0" icon="fa-regular fa-comments" text="发送消息开始调试对话" />
    <MessageItem v-for="(message, index) in state.messages" :key="index" :message="message" />
  </main>
</template>
