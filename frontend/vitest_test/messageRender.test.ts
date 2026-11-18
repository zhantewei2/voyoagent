import { beforeEach, describe, expect, test } from 'vitest'
import { beginTurn, handleEvent, resetState, state } from '@/stores/chat'
import type { AssistantMessage, ChatEvent, ChatSegment, UserMessage } from '@/types/chat'

type EventInput = ChatEvent | ChatEvent['type']

function dispatch(sequence: EventInput[]): void {
  sequence.forEach(event => handleEvent(typeof event === 'string' ? { type: event } : event))
}

function userMessage(index: number): UserMessage {
  const message = state.messages[index]
  if (!message || message.role !== 'user') throw new Error(`not a user message at ${index}`)
  return message
}

function assistantMessage(index: number): AssistantMessage {
  const message = state.messages[index]
  if (!message || message.role !== 'assistant') throw new Error(`not an assistant message at ${index}`)
  return message
}

function segOf<T extends ChatSegment['kind']>(segs: ChatSegment[], kind: T): Extract<ChatSegment, { kind: T }> {
  const seg = segs.find(item => item.kind === kind)
  if (!seg || seg.kind !== kind) throw new Error(`missing segment: ${kind}`)
  return seg as Extract<ChatSegment, { kind: T }>
}

beforeEach(() => resetState())

describe('大功能3：消息渲染数据组织', () => {
  test('用例3.1 消息列表结构与角色区分', () => {
    beginTurn('今天上海天气如何？')
    dispatch([{ type: 'text_start' }, { type: 'text_delta', content: '晴' }, 'done'])

    expect(state.messages).toHaveLength(2)
    expect(userMessage(0)).toEqual({ role: 'user', content: '今天上海天气如何？' })
    const assistant = assistantMessage(1)
    expect(assistant.role).toBe('assistant')
    expect(Array.isArray(assistant.segments)).toBe(true)
    expect(assistant.segments.length).toBeGreaterThan(0)
  })

  test('用例3.2 segments 顺序与事件一致', () => {
    beginTurn('q')
    dispatch([
      { type: 'thinking_start' },
      { type: 'thinking_delta', content: '想想' },
      'thinking_end',
      { type: 'tool_call', call_id: 'call_1', name: 'get_weather', arguments: '{"city":"上海"}' },
      { type: 'tool_result', call_id: 'call_1', name: 'get_weather', result: '晴' },
      'response_completed',
      'turn_end',
      { type: 'text_start' },
      { type: 'text_delta', content: '上海晴' },
    ])
    expect(assistantMessage(1).segments.map(seg => seg.kind)).toEqual(['thinking', 'tool', 'text'])
  })

  test('用例3.3 arguments 二次解析', () => {
    beginTurn('q')
    dispatch([{ type: 'tool_call', call_id: 'call_1', name: 'get_weather', arguments: '{"city":"上海"}' }])
    expect(segOf(assistantMessage(1).segments, 'tool').arguments).toEqual({ city: '上海' })

    // 非法 JSON 降级保留原始字符串，不抛错
    dispatch([{ type: 'tool_call', call_id: 'call_2', name: 'run_shell', arguments: 'not-json' }])
    expect(assistantMessage(1).segments[1].kind).toBe('tool')
    expect(segOf(assistantMessage(1).segments, 'tool').arguments).toEqual({ city: '上海' })
    const second = assistantMessage(1).segments[1]
    expect(second.kind === 'tool' && second.arguments).toBe('not-json')
    expect(state.errorMsg).toBe('')
  })

  test('用例3.4 done 后渲染终态完整', () => {
    beginTurn('今天上海天气如何？')
    dispatch([
      { type: 'thinking_start' },
      { type: 'thinking_delta', content: '用户想查上海天气，需要调用工具' },
      'thinking_end',
      { type: 'tool_call', call_id: 'call_a1b2c3', name: 'get_weather', arguments: '{"city":"上海"}' },
      { type: 'tool_result', call_id: 'call_a1b2c3', name: 'get_weather', result: '多雨转阴，21摄氏度' },
      { type: 'text_start' },
      { type: 'text_delta', content: '上海今天' },
      { type: 'done', content: '上海今天多雨转阴，21摄氏度。' },
    ])

    const segs = assistantMessage(1).segments
    expect(segOf(segs, 'thinking').content).toBe('用户想查上海天气，需要调用工具')

    const tool = segOf(segs, 'tool')
    expect(tool).toMatchObject({
      call_id: 'call_a1b2c3',
      name: 'get_weather',
      status: 'result',
      result: '多雨转阴，21摄氏度',
    })
    expect(tool.arguments).toEqual({ city: '上海' })

    expect(segOf(segs, 'text').content).toBe('上海今天多雨转阴，21摄氏度。')
    expect(state.streaming).toBe(false)
  })
})
