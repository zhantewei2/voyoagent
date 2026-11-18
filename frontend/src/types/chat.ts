import type { Id } from './common'

// 会话（POST /api/chats、GET /api/chats/{id} 出参）
export interface ChatInfo {
  chat_id: Id
  agent_id: Id
  title: string
  history: unknown[] // 原始 history 数组（user/assistant/function_call/function_call_output）
  created_at: string
  updated_at: string
}

// SSE 事件类型（api_contract.md schema）
export type ChatEventType =
  | 'run_start'
  | 'thinking_start'
  | 'thinking_delta'
  | 'thinking_end'
  | 'text_start'
  | 'text_delta'
  | 'tool_call'
  | 'tool_result'
  | 'tool_error'
  | 'response_completed'
  | 'turn_end'
  | 'done'
  | 'error'

export interface ChatEvent {
  type: ChatEventType
  content?: string
  call_id?: string
  name?: string
  arguments?: string
  result?: string
  error?: string
}

// 消息 segment：助手消息按事件出现顺序组织的有序片段
export interface ThinkingSegment {
  kind: 'thinking'
  content: string
}

export interface TextSegment {
  kind: 'text'
  content: string
}

export type ToolStatus = 'pending' | 'result' | 'error'

export interface ToolSegment {
  kind: 'tool'
  call_id: string
  name: string
  arguments: Record<string, unknown> | string
  status: ToolStatus
  result: string
}

export type ChatSegment = ThinkingSegment | TextSegment | ToolSegment

export interface UserMessage {
  role: 'user'
  content: string
}

export interface AssistantMessage {
  role: 'assistant'
  segments: ChatSegment[]
}

export type ChatMessage = UserMessage | AssistantMessage
