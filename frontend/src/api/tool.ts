import type { ToolItem } from '@/types/tool'
import { request } from './http'

export function listTools(): Promise<ToolItem[]> {
  return request<ToolItem[]>('/api/tools')
}
