<script setup lang="ts">
import { computed } from 'vue'
import type { ToolSegment, ToolStatus } from '@/types/chat'

const props = defineProps<{ segment: ToolSegment }>()

const STATUS_META: Record<ToolStatus, { label: string; tag: 'info' | 'success' | 'error' }> = {
  pending: { label: '调用中', tag: 'info' },
  result: { label: '结果', tag: 'success' },
  error: { label: '错误', tag: 'error' },
}

const meta = computed(() => STATUS_META[props.segment.status])
const argsText = computed(() =>
  typeof props.segment.arguments === 'string'
    ? props.segment.arguments
    : JSON.stringify(props.segment.arguments, null, 2),
)
</script>

<template>
  <div class="tool-call" :class="`tool-call--${segment.status}`" data-test="tool-call">
    <div class="tool-call__head">
      <span class="tool-call__name">{{ segment.name }}</span>
      <n-tag size="small" :type="meta.tag" :bordered="false">{{ meta.label }}</n-tag>
    </div>
    <pre class="tool-call__args">{{ argsText }}</pre>
    <div v-if="segment.status !== 'pending'" class="tool-call__result">{{ segment.result }}</div>
  </div>
</template>
