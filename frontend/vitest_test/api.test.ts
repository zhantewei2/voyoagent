import { afterEach, describe, expect, test, vi } from 'vitest'
import { createAgent, deleteAgent, listAgents, updateAgent } from '@/api/agent'
import { createChat, getChat, sendChatStream } from '@/api/chat'
import { createModel, listModels, updateModel } from '@/api/model'

//后端统一响应壳：{status_code, message}
function envelope(data: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => ({ status_code: status, message: data }),
  } as unknown as Response
}

function mockFetch(data: unknown, status = 200) {
  const spy = vi.fn(async (_url: string, _init?: RequestInit) => envelope(data, status))
  vi.stubGlobal('fetch', spy)
  return spy
}

type FetchSpy = ReturnType<typeof mockFetch>

function callAt(spy: FetchSpy, index: number): [_url: string, _init?: RequestInit] {
  const call = spy.mock.calls[index]
  if (!call) throw new Error(`call ${index} not found`)
  return call
}

function bodyOf(spy: FetchSpy, index: number): unknown {
  return JSON.parse(String(callAt(spy, index)[1]?.body ?? 'null'))
}

afterEach(() => vi.unstubAllGlobals())

describe('API 与类型层', () => {
  test('响应壳解包：message 即业务数据', async () => {
    const spy = mockFetch([{ id: '179393982080700010', name: 'm' }])
    const list = await listModels()
    expect(list).toEqual([{ id: '179393982080700010', name: 'm' }])
    expect(callAt(spy, 0)[0]).toBe('/api/models')
    expect(callAt(spy, 0)[1]).toBeUndefined()
  })

  test('模型接口请求拼装', async () => {
    const payload = { name: 'm1', model: 'x', base_url: 'http://b', api_key: 'k', description: '' }
    const spy = mockFetch({ id: '1', ...payload })

    await createModel(payload)
    expect(callAt(spy, 0)[0]).toBe('/api/models')
    expect(callAt(spy, 0)[1]?.method).toBe('POST')
    expect(bodyOf(spy, 0)).toEqual(payload)

    await updateModel('179393982080700010', payload)
    expect(callAt(spy, 1)[0]).toBe('/api/models/179393982080700010')
    expect(callAt(spy, 1)[1]?.method).toBe('PUT')
  })

  test('agent 接口请求拼装（id 保真为字符串）', async () => {
    const payload = {
      name: 'a',
      description: '',
      soul_prompt: 'soul',
      model_id: '179393982080700010',
      tool_names: ['read_file'],
      skill_ids: ['179393982181500091'],
      mcp_ids: [],
    }
    const spy = mockFetch({ id: '179393982356300040' })

    await createAgent(payload)
    expect(callAt(spy, 0)[0]).toBe('/api/agents')
    expect(bodyOf(spy, 0)).toEqual(payload)

    await updateAgent('179393982356300040', payload)
    expect(callAt(spy, 1)[0]).toBe('/api/agents/179393982356300040')

    await deleteAgent('179393982356300040')
    expect(callAt(spy, 2)[0]).toBe('/api/agents/179393982356300040')
    expect(callAt(spy, 2)[1]?.method).toBe('DELETE')
  })

  test('会话接口：创建与读取', async () => {
    const chat = {
      chat_id: '179393982400000001',
      agent_id: '179393982356300040',
      title: '',
      history: [],
      created_at: '',
      updated_at: '',
    }
    const spy = mockFetch(chat)

    await createChat('179393982356300040')
    expect(callAt(spy, 0)[0]).toBe('/api/chats')
    expect(bodyOf(spy, 0)).toEqual({ agent_id: '179393982356300040', title: '' })

    await getChat('179393982400000001')
    expect(callAt(spy, 1)[0]).toBe('/api/chats/179393982400000001')
  })

  test('chat 流接口：URL 带 agent 查询参数，body 含 chat_id/content/thinking', async () => {
    const frames = ['data: {"type":"done","content":"完"}\n\n']
    const encoder = new TextEncoder()
    const spy = vi.fn(async (_url: string, _init?: RequestInit) =>
      ({
        status: 200,
        ok: true,
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
      }) as unknown as Response,
    )
    vi.stubGlobal('fetch', spy)

    const events: string[] = []
    const result = await sendChatStream(
      { agentId: '179393982356300040', chatId: '179393982400000001', content: '你好', thinking: true },
      (e) => events.push(e.type),
    )
    expect(result.ok).toBe(true)
    expect(spy.mock.calls[0][0]).toBe('/api/chat?agent=179393982356300040')
    expect(JSON.parse(String(spy.mock.calls[0][1]?.body))).toEqual({
      chat_id: '179393982400000001',
      content: '你好',
      thinking: true,
    })
    expect(events).toEqual(['done'])
  })

  test('业务错误壳取 message 作为错误信息', async () => {
    const spy = vi.fn(async () => envelope('模型已被 agent 引用: a1', 400))
    vi.stubGlobal('fetch', spy)
    await expect(listAgents()).rejects.toThrow('模型已被 agent 引用: a1')
  })
})
