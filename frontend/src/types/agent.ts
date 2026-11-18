import type { Id } from './common'
import type { McpItem, McpState } from './mcp'
import type { ModelItem } from './model'
import type { SkillItem } from './skill'

export interface AgentItem {
  id: Id
  name: string
  description: string
  model_id: Id
  model_name: string
  tool_names: string[]
  skill_names: string[]
  mcp_names: string[]
  created_at: string
  updated_at: string
}

export interface AgentDetail {
  id: Id
  name: string
  description: string
  soul_prompt: string
  model_id: Id
  model: ModelItem | null
  tool_names: string[]
  skills: SkillItem[]
  mcps: McpItem[]
  mcp_states: McpState[]
  created_at: string
  updated_at: string
}

export interface AgentPayload {
  name: string
  description: string
  soul_prompt: string
  model_id: Id
  tool_names: string[]
  skill_ids: Id[]
  mcp_ids: Id[]
}
