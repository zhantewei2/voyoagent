import type { Id } from './common'

export interface ModelItem {
  id: Id
  name: string
  model: string
  base_url: string
  api_key: string // 脱敏值（保留后 4 位）
  description: string
  created_at: string
  updated_at: string
}

export interface ModelPayload {
  name: string
  model: string
  base_url: string
  api_key: string
  description: string
}
