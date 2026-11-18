import { describe, expect, test } from 'vitest'
import { createSseParser, type SseEvent } from '@/utils/sse'

const encoder = new TextEncoder()
const frame = (json: unknown) => `data: ${JSON.stringify(json)}\n\n`
const bytes = (text: string) => encoder.encode(text)
const types = (events: SseEvent[]) => events.map(e => e.type)

describe('大功能1：SSE 帧解析', () => {
  test('用例1.1 单帧与多帧解析', () => {
    const parser = createSseParser()
    expect(parser.push(bytes(frame({ type: 'run_start' })))).toEqual([{ type: 'run_start' }])

    const multi = parser.push(
      bytes(
        frame({ type: 'thinking_start' }) +
          frame({ type: 'thinking_delta', content: 'a' }) +
          frame({ type: 'thinking_end' }),
      ),
    )
    expect(multi).toEqual([
      { type: 'thinking_start' },
      { type: 'thinking_delta', content: 'a' },
      { type: 'thinking_end' },
    ])
  })

  test('用例1.2 半帧跨 chunk 缓冲拼接', () => {
    const parser = createSseParser()
    expect(parser.push(bytes('data: {"type":"text_del'))).toEqual([])
    expect(parser.push(bytes('ta","content":"hi"}\n\n'))).toEqual([{ type: 'text_delta', content: 'hi' }])
  })

  test('用例1.3 多字节 UTF-8 跨 chunk', () => {
    const text = 'data: {"type":"text_delta","content":"上海天气"}\n\n'
    const all = bytes(text)
    const cut = bytes('data: {"type":"text_delta","content":"').length + 1 // 落在“上”的 3 字节中间
    const parser = createSseParser()

    expect(parser.push(all.slice(0, cut))).toEqual([])
    expect(parser.push(all.slice(cut))).toEqual([{ type: 'text_delta', content: '上海天气' }])
  })

  test('用例1.4 帧前缀与混合噪声容错', () => {
    const parser = createSseParser()
    const noisy = ['event: ping\n\n', 'garbage without prefix\n\n', 'data: {oops}\n\n', frame({ type: 'run_start' })].join('')
    expect(parser.push(bytes(noisy))).toEqual([{ type: 'run_start' }])
  })

  test('用例1.5 完整契约事件序列回放', () => {
    // api_contract.md 响应示例（修正后顺序：turn_end 位于末轮 response_completed 之后、done 之前）
    const contractStream = [
      frame({ type: 'run_start' }),
      frame({ type: 'thinking_start' }),
      frame({ type: 'thinking_delta', content: '用户询问上海天气，需要调用工具' }),
      frame({ type: 'thinking_end' }),
      frame({ type: 'tool_call', call_id: 'call_a1b2c3', name: 'get_weather', arguments: '{"city":"上海"}' }),
      frame({ type: 'tool_result', call_id: 'call_a1b2c3', name: 'get_weather', result: '上海的天气为 多雨转阴， 21摄氏度' }),
      frame({ type: 'response_completed' }),
      frame({ type: 'thinking_start' }),
      frame({ type: 'thinking_delta', content: '拿到天气结果，组织回答' }),
      frame({ type: 'thinking_end' }),
      frame({ type: 'text_start' }),
      frame({ type: 'text_delta', content: '上海今天' }),
      frame({ type: 'text_delta', content: '多雨转阴，21摄氏度。' }),
      frame({ type: 'response_completed' }),
      frame({ type: 'turn_end' }),
      frame({ type: 'done', content: '上海今天多雨转阴，21摄氏度。' }),
    ].join('')

    const events = createSseParser().push(bytes(contractStream))
    expect(events).toHaveLength(16)
    expect(types(events)).toEqual([
      'run_start',
      'thinking_start',
      'thinking_delta',
      'thinking_end',
      'tool_call',
      'tool_result',
      'response_completed',
      'thinking_start',
      'thinking_delta',
      'thinking_end',
      'text_start',
      'text_delta',
      'text_delta',
      'response_completed',
      'turn_end',
      'done',
    ])
    expect((events[15] as { content: string }).content).toBe('上海今天多雨转阴，21摄氏度。')
  })

  test('用例1.6 流异常关闭不抛错', () => {
    const parser = createSseParser()
    expect(parser.push(bytes(frame({ type: 'run_start' })))).toHaveLength(1)
    expect(() => parser.push(bytes('data: {"type":"thinking_delta","content":"half'))).not.toThrow()
    expect(() => parser.end()).not.toThrow()
    // end 清空 buffer 后继续 push 不受残帧影响
    expect(parser.push(bytes(frame({ type: 'done', content: 'ok' })))).toEqual([{ type: 'done', content: 'ok' }])
  })
})
