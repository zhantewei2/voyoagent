// 内置工具（只读）
export interface ToolItem {
  type: string
  name: string
  description: string
  parameters: Record<string, unknown>
}
