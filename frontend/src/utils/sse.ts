// SSE 帧解析器：跨 chunk 缓冲拼接，按 \n\n 切帧，剥离 data: 前缀后 JSON.parse
export type SseEvent = Record<string, unknown>

export interface SseParser {
  push(chunk: Uint8Array | string): SseEvent[]
  end(): SseEvent[]
}

function parseFrame(frame: string): SseEvent | null {
  const line = frame.trim()
  if (!line.startsWith('data:')) return null
  const payload = line.slice(5).trim()
  if (!payload) return null
  try {
    const parsed: unknown = JSON.parse(payload)
    return parsed !== null && typeof parsed === 'object' ? (parsed as SseEvent) : null
  } catch {
    return null
  }
}

export function createSseParser(): SseParser {
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  return {
    push(chunk) {
      buffer += typeof chunk === 'string' ? chunk : decoder.decode(chunk, { stream: true })
      const events: SseEvent[] = []
      let idx = buffer.indexOf('\n\n')
      while (idx !== -1) {
        const event = parseFrame(buffer.slice(0, idx))
        if (event) events.push(event)
        buffer = buffer.slice(idx + 2)
        idx = buffer.indexOf('\n\n')
      }
      return events
    },
    end() {
      // 流关闭：丢弃残帧（契约约定断线无终止帧），不抛错
      buffer = ''
      return []
    },
  }
}
