import type { Id } from './common'

export interface McpItem {
  id: Id
  name: string
  description: string
  command: string
  args: string[]
  url: string
  created_at: string
  updated_at: string
}

export interface McpPayload {
  name: string
  description: string
  command: string
  args: string[]
  url: string
}

export type McpStateType = 'loading' | 'ready' | 'error'

// agent 实例内的 MCP 运行时状态（list_mcp 快照）
export interface McpState {
  name: string
  state: McpStateType
  command: string
  args: string[]
  url: string
  error: string
  tools: string[]
}
