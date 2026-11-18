// 通用请求：统一解包 {status_code, message} 响应壳，错误信息优先取 message
export const JSON_HEADERS = { 'Content-Type': 'application/json' }

interface Envelope {
  status_code: number
  message: unknown
}

function unwrap<T>(body: unknown): T {
  if (body && typeof body === 'object' && 'status_code' in body && 'message' in body) {
    return (body as Envelope).message as T
  }
  return body as T
}

//错误信息优先取后端 message（YoHttpException 统一壳），兼容 detail
async function errorDetail(res: Response): Promise<string> {
  const fallback = `请求失败（HTTP ${res.status}）`
  try {
    const body = (await res.json()) as { message?: unknown; detail?: unknown }
    if (typeof body?.message === 'string' && body.message) return body.message
    if (typeof body?.detail === 'string') return body.detail
    if (Array.isArray(body?.detail)) {
      return body.detail.map((d) => (d as { msg?: string })?.msg ?? '').join('; ') || fallback
    }
  } catch {
    // 响应体不是 JSON，用默认文案
  }
  return fallback
}

export async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) {
    throw new Error(await errorDetail(res))
  }
  return unwrap<T>(await res.json())
}
