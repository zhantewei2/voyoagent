<script setup lang="ts">
import { computed, reactive } from 'vue'
import { sendMessage, setThinking, state as chatState } from '@/stores/chat'

const props = defineProps<{ disabled?: boolean }>()

const local = reactive({ draft: '' })
const canSend = computed(
  () => !props.disabled && !chatState.streaming && local.draft.trim().length > 0,
)

async function handleSend(): Promise<void> {
  if (!canSend.value) return
  const text = local.draft
  local.draft = ''
  await sendMessage(text)
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    void handleSend()
  }
}
</script>

<template>
  <footer class="chat-input">
    <div class="chat-input__main">
      <n-input
        v-model:value="local.draft"
        type="textarea"
        class="chat-input__box"
        placeholder="输入消息，Enter 发送，Shift + Enter 换行"
        :autosize="{ minRows: 1, maxRows: 4 }"
        :disabled="props.disabled"
        data-test="chat-input"
        @keydown="onKeydown"
      />
      <div class="chat-input__bar">
        <n-tooltip trigger="hover">
          <template #trigger>
            <label class="chat-input__thinking" data-test="thinking-toggle">
              <input
                type="checkbox"
                :checked="chatState.thinking"
                @change="setThinking(($event.target as HTMLInputElement).checked)"
              />
              启用思考
            </label>
          </template>
          开启后模型先推理再回答（较慢），并展示思考过程
        </n-tooltip>
        <n-button
          type="primary"
          class="chat-input__send"
          :disabled="!canSend"
          :loading="chatState.streaming"
          data-test="send-button"
          @click="handleSend"
        >
          <i class="fa-regular fa-paper-plane" />&nbsp;发送
        </n-button>
      </div>
    </div>
  </footer>
</template>
