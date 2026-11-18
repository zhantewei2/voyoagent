import type { AgentDetail, AgentItem, AgentPayload } from '@/types/agent'
import type { Id } from '@/types/common'
import { JSON_HEADERS, request } from './http'

export function listAgents(): Promise<AgentItem[]> {
  return request<AgentItem[]>('/api/agents')
}

export function getAgent(id: Id): Promise<AgentDetail> {
  return request<AgentDetail>(`/api/agents/${encodeURIComponent(id)}`)
}

export function createAgent(payload: AgentPayload): Promise<AgentItem> {
  return request<AgentItem>('/api/agents', {
    method: 'POST',
    headers: JSON_HEADERS,
    body: JSON.stringify(payload),
  })
}

export function updateAgent(id: Id, payload: AgentPayload): Promise<AgentItem> {
  return request<AgentItem>(`/api/agents/${encodeURIComponent(id)}`, {
    method: 'PUT',
    headers: JSON_HEADERS,
    body: JSON.stringify(payload),
  })
}

export function deleteAgent(id: Id): Promise<unknown> {
  return request(`/api/agents/${encodeURIComponent(id)}`, { method: 'DELETE' })
}
