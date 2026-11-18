import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'
import {
  beginTurn,
  handleEvent,
  historyToMessages,
  initSession,
  resetState,
  sendMessage,
  setThinking,
  state,
} from '@/stores/chat'
import type { AssistantMessage, ChatEvent, TextSegment, ToolSegment, UserMessage } from '@/types/chat'

const frame = (json: unknown) => `data: ${JSON.stringify(json)}\n\n`
const encoder = new TextEncoder()

function sseResponse(frames: string[], status = 200): Response {
  return {
    status,
    ok: status >= 200 && status < 300,
    body: {
      getReader: () => {
        let i = 0
        return {
          read: async () =>
            i < frames.length
              ? { done: false, value: encoder.encode(frames[i++]) }
              : { done: true, value: undefined },
          cancel: async () => undefined,
        }
      },
    },
  } as unknown as Response
}

function assistant(): AssistantMessage {
  const last = state.messages[state.messages.length - 1]
  if (!last || last.role !== 'assistant') throw new Error('no active assistant message')
  return last
}

function dispatch(sequence: ChatEvent[]): void {
  sequence.forEach(handleEvent)
}

beforeEach(() => {
  resetState()
  initSession('agent-1', 'chat-1')
})
afterEach(() => vi.unstubAllGlobals())

describe('chat store 状态流转', () => {
  test('发送进入流式态并携带会话参数', async () => {
    let resolveFetch!: (res: Response) => void
    const spy = vi.fn(
      (_url: string, _init?: RequestInit) => new Promise<Response>(resolve => (resolveFetch = resolve)),
    )
    vi.stubGlobal('fetch', spy)

    setThinking(true)
    const pending = sendMessage('你好')
    expect(state.streaming).toBe(true)
    expect(state.messages.map(m => m.role)).toEqual(['user', 'assistant'])
    expect(state.messages[0]).toEqual({ role: 'user', content: '你好' })

    resolveFetch(sseResponse([frame({ type: 'done', content: '完成' })]))
    await pending
    expect(state.streaming).toBe(false)

    expect(spy.mock.calls[0][0]).toBe('/api/chat?agent=agent-1')
    expect(JSON.parse(String(spy.mock.calls[0][1]?.body))).toEqual({
      chat_id: 'chat-1',
      content: '你好',
      thinking: true,
    })
  })

  test('thinking 开关随请求下发', async () => {
    const spy = vi.fn(async (_url: string, _init?: RequestInit) =>
      sseResponse([frame({ type: 'done', content: 'ok' })]),
    )
    vi.stubGlobal('fetch', spy)
    setThinking(false)
    await sendMessage('hi')
    expect(JSON.parse(String(spy.mock.calls[0][1]?.body)).thinking).toBe(false)
  })

  test('thinking 增量累积', () => {
    beginTurn('问题')
    dispatch([
      { type: 'thinking_start' },
      { type: 'thinking_delta', content: '先想' },
      { type: 'thinking_delta', content: '一步' },
      { type: 'thinking_end' },
    ])
    expect(assistant().segments).toEqual([{ kind: 'thinking', content: '先想一步' }])
  })

  test('text 增量累积', () => {
    beginTurn('问题')
    dispatch([
      { type: 'text_start' },
      { type: 'text_delta', content: '上海' },
      { type: 'text_delta', content: '今天晴' },
    ])
    expect(assistant().segments).toEqual([{ kind: 'text', content: '上海今天晴' }])
  })

  test('工具事件 call_id 匹配', () => {
    beginTurn('问题')
    dispatch([
      { type: 'tool_call', call_id: 'call_1', name: 'get_weather', arguments: '{"city":"上海"}' },
      { type: 'tool_call', call_id: 'call_2', name: 'read_file', arguments: '{"path":"a.txt"}' },
      { type: 'tool_result', call_id: 'call_1', name: 'get_weather', result: '晴' },
      { type: 'tool_error', call_id: 'call_2', name: 'read_file', error: 'timeout' },
    ])
    const segs = assistant().segments as ToolSegment[]
    expect(segs[0]).toMatchObject({ kind: 'tool', call_id: 'call_1', status: 'result', result: '晴' })
    expect(segs[1]).toMatchObject({ kind: 'tool', call_id: 'call_2', status: 'error', result: 'timeout' })
  })

  test('done 定稿并结束', () => {
    beginTurn('问题')
    dispatch([
      { type: 'text_start' },
      { type: 'text_delta', content: '上海今天' },
      { type: 'text_delta', content: '多雨' },
      { type: 'done', content: '上海今天多雨转阴，21摄氏度。' },
    ])
    const texts = assistant().segments.filter(s => s.kind === 'text') as TextSegment[]
    expect(texts).toHaveLength(1)
    expect(texts[0].content).toBe('上海今天多雨转阴，21摄氏度。')
    expect(state.streaming).toBe(false)
  })

  test('error 事件处理', () => {
    beginTurn('问题')
    dispatch([{ type: 'error', content: 'Connection error.' }])
    expect(state.errorMsg).toContain('Connection error.')
    expect(state.streaming).toBe(false)
  })

  test('409 处理', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => sseResponse([], 409)))
    await sendMessage('hi')
    expect(state.errorMsg).toContain('忙碌')
    expect(state.messages).toEqual([{ role: 'user', content: 'hi' }])
    expect(state.streaming).toBe(false)
  })

  test('历史恢复：user/assistant/工具往返重组', () => {
    const messages = historyToMessages([
      { role: 'user', content: '今天天气？' },
      { type: 'function_call', call_id: 'c1', name: 'get_weather', arguments: '{"city":"上海"}' },
      { type: 'function_call_output', call_id: 'c1', output: '晴' },
      { role: 'assistant', content: '今天晴。' },
      { role: 'user', content: '明天呢' },
      { role: 'assistant', content: '明天多云。' },
    ])
    expect(messages).toHaveLength(4)
    expect(messages[0]).toEqual({ role: 'user', content: '今天天气？' } satisfies UserMessage)
    const first = messages[1] as AssistantMessage
    expect(first.segments.map(s => s.kind)).toEqual(['tool', 'text'])
    expect(first.segments[0]).toMatchObject({ kind: 'tool', call_id: 'c1', status: 'result', result: '晴' })
    expect(messages[2]).toEqual({ role: 'user', content: '明天呢' } satisfies UserMessage)
    expect((messages[3] as AssistantMessage).segments).toEqual([{ kind: 'text', content: '明天多云。' }])
  })
})
