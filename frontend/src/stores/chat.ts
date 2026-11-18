import { reactive } from 'vue'
import { sendChatStream } from '@/api/chat'
import type {
  AssistantMessage,
  ChatEvent,
  ChatMessage,
  ChatSegment,
  ToolSegment,
  UserMessage,
} from '@/types/chat'
import type { Id } from '@/types/common'
import { toId } from '@/types/common'

export interface ChatState {
  messages: ChatMessage[]
  streaming: boolean
  errorMsg: string
  agentId: Id
  chatId: Id
  thinking: boolean // true 开启模型思考（effort=low），false 关闭（effort=none）
}

export const state = reactive<ChatState>({
  messages: [],
  streaming: false,
  errorMsg: '',
  agentId: '',
  chatId: '',
  thinking: true,
})

export function resetState(): void {
  state.messages = []
  state.streaming = false
  state.errorMsg = ''
}

//绑定会话：进入详情页拿到 chat_id 后调用，history 为空则只重置消息
export function initSession(agentId: Id, chatId: Id, history: unknown[] = []): void {
  state.agentId = toId(agentId)
  state.chatId = toId(chatId)
  state.streaming = false
  state.errorMsg = ''
  state.messages = historyToMessages(history)
}

export function setThinking(value: boolean): void {
  state.thinking = value
}

// 开始一轮对话：追加用户消息与助手占位消息并进入流式态
export function beginTurn(content: string): void {
  if (state.streaming) return
  state.errorMsg = ''
  state.messages.push({ role: 'user', content })
  state.messages.push({ role: 'assistant', segments: [] })
  state.streaming = true
}

function currentAssistant(): AssistantMessage | null {
  const last = state.messages[state.messages.length - 1]
  return last && last.role === 'assistant' ? last : null
}

function lastSegment<K extends ChatSegment['kind']>(
  assistant: AssistantMessage,
  kind: K,
): Extract<ChatSegment, { kind: K }> | null {
  for (let i = assistant.segments.length - 1; i >= 0; i--) {
    const seg = assistant.segments[i]
    if (seg.kind === kind) return seg as Extract<ChatSegment, { kind: K }>
  }
  return null
}

function findToolSegment(assistant: AssistantMessage, callId: string): ToolSegment | null {
  for (let i = assistant.segments.length - 1; i >= 0; i--) {
    const seg = assistant.segments[i]
    if (seg.kind === 'tool' && seg.call_id === callId) return seg
  }
  return null
}

function parseArguments(raw?: string): Record<string, unknown> | string {
  if (!raw) return {}
  try {
    const parsed: unknown = JSON.parse(raw)
    return parsed !== null && typeof parsed === 'object' ? (parsed as Record<string, unknown>) : raw
  } catch {
    return raw
  }
}

function finalizeWithDone(content: string): void {
  const assistant = currentAssistant()
  if (assistant) {
    const seg = lastSegment(assistant, 'text')
    if (seg) seg.content = content
    else if (content) assistant.segments.push({ kind: 'text', content })
  }
  state.streaming = false
}

// SSE 事件驱动状态流转；无活动助手消息时忽略
export function handleEvent(event: ChatEvent): void {
  const assistant = currentAssistant()
  if (!assistant) return
  switch (event.type) {
    case 'thinking_start':
      assistant.segments.push({ kind: 'thinking', content: '' })
      break
    case 'thinking_delta': {
      const seg = lastSegment(assistant, 'thinking')
      if (seg) seg.content += event.content ?? ''
      break
    }
    case 'text_start':
      assistant.segments.push({ kind: 'text', content: '' })
      break
    case 'text_delta': {
      const seg = lastSegment(assistant, 'text')
      if (seg) seg.content += event.content ?? ''
      break
    }
    case 'tool_call':
      assistant.segments.push({
        kind: 'tool',
        call_id: event.call_id ?? '',
        name: event.name ?? '',
        arguments: parseArguments(event.arguments),
        status: 'pending',
        result: '',
      })
      break
    case 'tool_result': {
      const seg = findToolSegment(assistant, event.call_id ?? '')
      if (seg) {
        seg.status = 'result'
        seg.result = event.result ?? ''
      }
      break
    }
    case 'tool_error': {
      const seg = findToolSegment(assistant, event.call_id ?? '')
      if (seg) {
        seg.status = 'error'
        seg.result = event.error ?? ''
      }
      break
    }
    case 'done':
      // done.content 为本次对话最终全文，直接定稿
      finalizeWithDone(event.content ?? '')
      break
    case 'error':
      state.errorMsg = event.content || '服务异常，请稍后重试'
      state.streaming = false
      break
    default:
      // run_start / thinking_end / response_completed / turn_end 不驱动状态
      break
  }
}

export async function sendMessage(content: string, signal?: AbortSignal): Promise<void> {
  const text = content.trim()
  if (!text || state.streaming) return
  beginTurn(text)

  const result = await sendChatStream(
    { agentId: state.agentId, chatId: state.chatId, content: text, thinking: state.thinking },
    handleEvent,
    signal,
  )
  if (!result.ok) {
    state.errorMsg = result.errorMsg ?? '请求失败，请稍后重试'
    // 失败且助手消息尚无内容时移除占位（409 / 网络失败不污染消息列表）
    const assistant = currentAssistant()
    if (assistant && assistant.segments.length === 0) state.messages.pop()
  }
  // 流关闭但未收到 done/error（断线）：补提示并结束
  if (state.streaming) {
    state.errorMsg = state.errorMsg || '连接中断，本轮对话已终止'
    state.streaming = false
  }
}

// ---- 历史恢复：PG history（Responses 消息序列）→ 消息列表 ----

export function historyToMessages(history: unknown[]): ChatMessage[] {
  const messages: ChatMessage[] = []
  let assistant: AssistantMessage | null = null

  const ensureAssistant = (): AssistantMessage => {
    if (!assistant) {
      assistant = { role: 'assistant', segments: [] }
      messages.push(assistant)
    }
    return assistant
  }
  const findTool = (callId: string): ToolSegment | null => {
    for (const message of messages) {
      if (message.role !== 'assistant') continue
      const seg = findToolSegment(message, callId)
      if (seg) return seg
    }
    return null
  }

  for (const raw of history) {
    const item = (raw ?? {}) as Record<string, unknown>
    const type = typeof item.type === 'string' ? item.type : 'message'
    if (type === 'function_call') {
      ensureAssistant().segments.push({
        kind: 'tool',
        call_id: toId(item.call_id),
        name: String(item.name ?? ''),
        arguments: parseArguments(String(item.arguments ?? '')),
        status: 'pending',
        result: '',
      })
    } else if (type === 'function_call_output') {
      const seg = findTool(toId(item.call_id))
      if (seg) {
        seg.status = 'result'
        seg.result = String(item.output ?? '')
      }
    } else if (type === 'reasoning') {
      continue
    } else {
      const content = typeof item.content === 'string' ? item.content : ''
      if (item.role === 'user') {
        messages.push({ role: 'user', content } satisfies UserMessage)
        assistant = null
      } else if (item.role === 'assistant' && content) {
        ensureAssistant().segments.push({ kind: 'text', content })
      }
    }
  }
  return messages
}
