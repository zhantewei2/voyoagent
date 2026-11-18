import type { Id } from '@/types/common'
import type { McpItem, McpPayload } from '@/types/mcp'
import { JSON_HEADERS, request } from './http'

export function listMcp(): Promise<McpItem[]> {
  return request<McpItem[]>('/api/mcp')
}

export function createMcp(payload: McpPayload): Promise<McpItem> {
  return request<McpItem>('/api/mcp', {
    method: 'POST',
    headers: JSON_HEADERS,
    body: JSON.stringify(payload),
  })
}

export function updateMcp(id: Id, payload: McpPayload): Promise<McpItem> {
  return request<McpItem>(`/api/mcp/${encodeURIComponent(id)}`, {
    method: 'PUT',
    headers: JSON_HEADERS,
    body: JSON.stringify(payload),
  })
}

export function deleteMcp(id: Id): Promise<unknown> {
  return request(`/api/mcp/${encodeURIComponent(id)}`, { method: 'DELETE' })
}
