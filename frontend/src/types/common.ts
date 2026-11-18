// 公共类型约定：后端 bigint 主键（>2^53）在 JSON 中序列化为字符串，Id 一律按字符串处理
export type Id = string

export function toId(value: unknown): Id {
  return String(value ?? '')
}
