import type { Id } from './common'

export interface SkillItem {
  id: Id
  name: string
  description: string
  created_at: string
  updated_at: string
}

export interface SkillDetail extends SkillItem {
  content: string // 含 frontmatter 的技能全文
}

export interface SkillPayload {
  name: string
  description: string
  content: string
}
