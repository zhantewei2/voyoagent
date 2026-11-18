import type { Id } from '@/types/common'
import type { SkillDetail, SkillItem, SkillPayload } from '@/types/skill'
import { JSON_HEADERS, request } from './http'

export function listSkills(): Promise<SkillItem[]> {
  return request<SkillItem[]>('/api/skills')
}

export function getSkill(id: Id): Promise<SkillDetail> {
  return request<SkillDetail>(`/api/skills/${encodeURIComponent(id)}`)
}

export function createSkill(payload: SkillPayload): Promise<SkillDetail> {
  return request<SkillDetail>('/api/skills', {
    method: 'POST',
    headers: JSON_HEADERS,
    body: JSON.stringify(payload),
  })
}

export function updateSkill(id: Id, payload: SkillPayload): Promise<SkillDetail> {
  return request<SkillDetail>(`/api/skills/${encodeURIComponent(id)}`, {
    method: 'PUT',
    headers: JSON_HEADERS,
    body: JSON.stringify(payload),
  })
}

export function deleteSkill(id: Id): Promise<unknown> {
  return request(`/api/skills/${encodeURIComponent(id)}`, { method: 'DELETE' })
}
