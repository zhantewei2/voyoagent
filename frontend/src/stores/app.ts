import { reactive } from 'vue'
import type { Id } from '@/types/common'
import { toId } from '@/types/common'

export type ViewKey = 'model' | 'skill' | 'mcp' | 'tool' | 'agent' | 'agentDetail'

export interface AppState {
  activeView: ViewKey
  currentAgentId: Id // agentDetail 视图的当前 agent
  errorMsg: string
}

export const state = reactive<AppState>({
  activeView: 'agent',
  currentAgentId: '',
  errorMsg: '',
})

export function setView(view: ViewKey): void {
  state.activeView = view
}

//进入 agent 详情调试页
export function openAgentDetail(agentId: Id): void {
  state.currentAgentId = toId(agentId)
  state.activeView = 'agentDetail'
}

export function clearError(): void {
  state.errorMsg = ''
}

//各视图操作失败统一上报到全局提示
export function showError(e: unknown, fallback: string): void {
  state.errorMsg = e instanceof Error ? e.message : fallback
}
