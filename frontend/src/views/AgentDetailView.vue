<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { chatApiUrl, createChat, getChat, CHAT_EVENT_DOCS } from '@/api/chat'
import { getAgent } from '@/api/agent'
import AgentFormModal from '@/components/AgentFormModal.vue'
import ChatInput from '@/components/ChatInput.vue'
import ChatMessages from '@/components/ChatMessages.vue'
import { setView, showError, state as appState } from '@/stores/app'
import { initSession } from '@/stores/chat'
import type { AgentDetail } from '@/types/agent'
import type { McpState, McpStateType } from '@/types/mcp'
import { iconTitle } from '@/utils/ui'

const detail = ref<AgentDetail | null>(null)
const showForm = ref(false)
const showApi = ref(false)
const sessionReady = ref(false)
const sessionError = ref('')
const copied = ref(false)

const agentId = computed(() => appState.currentAgentId)

onMounted(() => void bootstrap())

//进入详情页：拉取配置 → 创建 chat_id → 恢复会话历史
async function bootstrap(): Promise<void> {
  try {
    detail.value = await getAgent(agentId.value)
  } catch (e) {
    showError(e, '读取 agent 详情失败')
    return
  }
  await createSession()
}

//会话创建失败不兜底空 chat_id：禁用输入并提供重试
async function createSession(): Promise<void> {
  sessionError.value = ''
  sessionReady.value = false
  try {
    const chat = await createChat(agentId.value)
    const saved = await getChat(String(chat.chat_id))
    initSession(agentId.value, saved.chat_id, saved.history)
    sessionReady.value = true
  } catch (e) {
    sessionError.value = e instanceof Error ? e.message : '创建会话失败'
  }
}

function back(): void {
  setView('agent')
}

const MCP_STATE_LABEL: Record<McpStateType, string> = {
  loading: '加载中',
  ready: '已连接',
  error: '异常',
}
const MCP_STATE_TAG: Record<McpStateType, 'default' | 'success' | 'error'> = {
  loading: 'default',
  ready: 'success',
  error: 'error',
}

function mcpStateOf(name: string): McpState | undefined {
  return detail.value?.mcp_states.find((m) => m.name === name)
}

async function onSaved(): Promise<void> {
  try {
    detail.value = await getAgent(agentId.value)
  } catch (e) {
    showError(e, '刷新 agent 详情失败')
  }
}

const apiUrl = computed(() => chatApiUrl(agentId.value))

async function copyUrl(): Promise<void> {
  try {
    await navigator.clipboard.writeText(apiUrl.value)
    copied.value = true
    setTimeout(() => (copied.value = false), 1500)
  } catch {
    showError(new Error('复制失败，请手动复制'), '复制失败，请手动复制')
  }
}

const eventDocs = CHAT_EVENT_DOCS

const fetchSample = computed(
  () => `fetch("${apiUrl.value}", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ chat_id: "<chat_id>", content: "你好", thinking: true }),
}).then((res) => {
  // res.body 为 SSE 流，逐帧 data: {json}
})`,
)

const curlSample = computed(
  () => `curl -N -X POST '${apiUrl.value}' \\
  -H 'Content-Type: application/json' \\
  -d '{"chat_id":"<chat_id>","content":"你好","thinking":true}'`,
)
</script>

<template>
  <section class="detail">
    <header class="view__header detail__header">
      <div class="detail__title">
        <n-button size="small" data-test="detail-back" @click="back">
          <i class="fa-solid fa-arrow-left" />&nbsp;返回列表
        </n-button>
        <span class="view__title">{{ detail?.name ?? 'agent 详情' }}</span>
      </div>
      <n-button data-test="detail-api" @click="showApi = true">
        <i class="fa-solid fa-code" />&nbsp;API 接口
      </n-button>
    </header>

    <div class="detail__body">
      <aside class="detail__config panel">
        <div class="panel__title">Agent 配置</div>
        <div class="form-stack" data-test="detail-config">
          <div class="form-stack__label">名称 / 描述</div>
          <div>{{ detail?.name }} — {{ detail?.description || '无描述' }}</div>

          <div class="form-stack__label">角色提示词（追加在固定系统提示之后）</div>
          <pre class="detail-pre">{{ detail?.soul_prompt || '（未设置）' }}</pre>

          <div class="form-stack__label">模型</div>
          <div>{{ detail?.model ? `${detail.model.name}（${detail.model.model}）` : '—' }}</div>

          <div class="form-stack__label">工具</div>
          <div class="table__mono">{{ detail?.tool_names.join('、') || '—' }}</div>

          <div class="form-stack__label">Skill</div>
          <div>{{ detail?.skills.map((s) => s.name).join('、') || '—' }}</div>

          <div class="form-stack__label">MCP</div>
          <div v-for="mcp in detail?.mcps ?? []" :key="mcp.id" class="detail__mcp">
            {{ mcp.name }}
            <n-tooltip v-if="mcpStateOf(mcp.name)?.state === 'error' && mcpStateOf(mcp.name)?.error" trigger="hover">
              <template #trigger>
                <n-tag size="small" type="error">异常</n-tag>
              </template>
              {{ mcpStateOf(mcp.name)?.error }}
            </n-tooltip>
            <n-tag
              v-else
              size="small"
              :type="MCP_STATE_TAG[mcpStateOf(mcp.name)?.state ?? 'loading']"
            >
              {{ MCP_STATE_LABEL[mcpStateOf(mcp.name)?.state ?? 'loading'] }}
            </n-tag>
          </div>
          <div v-if="(detail?.mcps.length ?? 0) === 0">—</div>

          <n-button size="small" type="primary" data-test="detail-edit" @click="showForm = true">
            编辑配置
          </n-button>
        </div>
      </aside>

      <main class="detail__chat panel">
        <div class="panel__title">对话调试</div>
        <n-alert v-if="sessionError" type="error" class="view__hint" data-test="session-error">
          {{ sessionError }}
          <n-button size="small" data-test="session-retry" @click="createSession">
            重试创建会话
          </n-button>
        </n-alert>
        <ChatMessages />
        <ChatInput :disabled="!sessionReady" />
      </main>
    </div>

    <AgentFormModal v-model:show="showForm" :agent="detail" @saved="onSaved" />

    <n-modal v-model:show="showApi" preset="card" :title="iconTitle('fa-solid fa-code', 'API 接口')" class="agent-modal">
      <div class="form-stack" data-test="api-modal">
        <div class="form-stack__label">对外 chat 接口（仅 stream）</div>
        <div class="api-url-row">
          <n-input :value="apiUrl" readonly data-test="api-url" />
          <n-button size="small" title="复制" @click="copyUrl">
            <i class="fa-regular fa-copy" />&nbsp;{{ copied ? '已复制' : '复制' }}
          </n-button>
        </div>

        <div class="form-stack__label">调用说明</div>
        <ul class="api-doc">
          <li>仅支持 SSE 流式（text/event-stream），事件格式见下表。</li>
          <li>入参（JSON body）：<code>chat_id</code>（会话 id）、<code>content</code>（消息内容）、<code>thinking</code>（可选，true 开启模型思考（effort=low），默认 false；调试界面默认开启）。</li>
          <li>无 chat_id 时先调用 <code>POST /api/chats</code>，body <code>{"agent_id": "{{ agentId }}"}</code>，返回 <code>{chat_id}</code>。</li>
          <li>带同一 chat_id 续聊时，服务端把该会话历史推入上下文；历史持久化在服务端。</li>
        </ul>

        <div class="form-stack__label">事件格式（data: {json}，每帧含 type）</div>
        <table class="table">
          <thead>
            <tr><th>type</th><th>说明</th></tr>
          </thead>
          <tbody>
            <tr v-for="[type, desc] in eventDocs" :key="type">
              <td class="table__mono">{{ type }}</td>
              <td>{{ desc }}</td>
            </tr>
          </tbody>
        </table>

        <div class="form-stack__label">fetch 示例</div>
        <pre class="detail-pre">{{ fetchSample }}</pre>

        <div class="form-stack__label">curl 示例</div>
        <pre class="detail-pre">{{ curlSample }}</pre>
      </div>
    </n-modal>
  </section>
</template>
