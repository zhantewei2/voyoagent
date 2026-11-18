import type { ChatEvent, ChatInfo } from '@/types/chat'
import type { Id } from '@/types/common'
import { createSseParser, type SseEvent } from '@/utils/sse'
import { JSON_HEADERS, request } from './http'

export interface SendOptions {
  agentId: Id
  chatId: Id
  content: string
  thinking: boolean
}

// 对外 chat SSE 事件说明（API 弹窗与帮助手册共用）
export const CHAT_EVENT_DOCS: readonly (readonly [string, string])[] = [
  ['run_start', '一轮 run 开始'],
  ['thinking_start / thinking_delta / thinking_end', '思考流开始 / 增量 / 结束'],
  ['text_start / text_delta', '正文流开始 / 增量'],
  ['tool_call', '工具调用（call_id、name、arguments）'],
  ['tool_result / tool_error', '工具结果 / 工具错误（call_id、name、result / error）'],
  ['response_completed', '本轮模型响应流结束'],
  ['turn_end', '一轮工具回传完成'],
  ['done', 'run 结束（content 为最终全文）'],
  ['error', '出错（content 为错误信息）'],
] as const

export interface SendResult {
  ok: boolean
  busy?: boolean
  errorMsg?: string
}

// 对外 chat 接口地址（域名取当前域名，路径固定 + ?agent={agentId}），用于 API 弹窗展示
export function chatApiUrl(agentId: Id): string {
  return `${location.origin}${chatPath(agentId)}`
}

//请求用相对路径，与其它接口一致
function chatPath(agentId: Id): string {
  return `/api/chat?agent=${encodeURIComponent(agentId)}`
}

export function createChat(agentId: Id, title = ''): Promise<ChatInfo> {
  return request<ChatInfo>('/api/chats', {
    method: 'POST',
    headers: JSON_HEADERS,
    body: JSON.stringify({ agent_id: agentId, title }),
  })
}

export function getChat(chatId: Id): Promise<ChatInfo> {
  return request<ChatInfo>(`/api/chats/${encodeURIComponent(chatId)}`)
}

function toChatEvent(frame: SseEvent): ChatEvent | null {
  return typeof frame.type === 'string' ? (frame as unknown as ChatEvent) : null
}

// POST /api/chat?agent={agentId}：fetch + ReadableStream 手动解析 SSE（EventSource 不支持 POST）
export async function sendChatStream(
  options: SendOptions,
  onEvent: (event: ChatEvent) => void,
  signal?: AbortSignal,
): Promise<SendResult> {
  let res: Response
  try {
    res = await fetch(chatPath(options.agentId), {
      method: 'POST',
      headers: JSON_HEADERS,
      body: JSON.stringify({
        chat_id: options.chatId,
        content: options.content,
        thinking: options.thinking,
      }),
      signal,
    })
  } catch {
    return { ok: false, errorMsg: '网络异常，请检查后端服务后重试' }
  }

  if (res.status === 409) return { ok: false, busy: true, errorMsg: 'agent 忙碌，请稍后再试' }
  if (!res.ok || !res.body) {
    // 业务错误壳：{status_code, message}
    let msg = `请求失败（HTTP ${res.status}）`
    try {
      const body = (await res.json()) as { message?: unknown }
      if (typeof body?.message === 'string' && body.message) msg = body.message
    } catch {
      // 非 JSON 响应体，用默认文案
    }
    return { ok: false, errorMsg: msg }
  }
  const reader = res.body.getReader()
  const parser = createSseParser()
  try {
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      for (const frame of parser.push(value)) {
        const event = toChatEvent(frame)
        if (!event) continue
        onEvent(event)
        if (event.type === 'done' || event.type === 'error') {
          //终止帧即收：cancel 释放底层连接，不再读残余流
          await reader.cancel().catch(() => undefined)
          return { ok: true }
        }
      }
    }
    parser.end()
    await reader.cancel().catch(() => undefined)
    return { ok: true }
  } catch {
    return { ok: false, errorMsg: '连接中断，本轮对话已终止' }
  }
}
