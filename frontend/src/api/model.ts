import type { Id } from '@/types/common'
import type { ModelItem, ModelPayload } from '@/types/model'
import { JSON_HEADERS, request } from './http'

export function listModels(): Promise<ModelItem[]> {
  return request<ModelItem[]>('/api/models')
}

export function createModel(payload: ModelPayload): Promise<ModelItem> {
  return request<ModelItem>('/api/models', {
    method: 'POST',
    headers: JSON_HEADERS,
    body: JSON.stringify(payload),
  })
}

export function updateModel(id: Id, payload: ModelPayload): Promise<ModelItem> {
  return request<ModelItem>(`/api/models/${encodeURIComponent(id)}`, {
    method: 'PUT',
    headers: JSON_HEADERS,
    body: JSON.stringify(payload),
  })
}

export function deleteModel(id: Id): Promise<unknown> {
  return request(`/api/models/${encodeURIComponent(id)}`, { method: 'DELETE' })
}
