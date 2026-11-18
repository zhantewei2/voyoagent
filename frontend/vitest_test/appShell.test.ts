import { afterEach, describe, expect, test, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import App from '@/App.vue'

//视图 onMounted 会拉列表：统一返回空壳响应
function stubFetch(): void {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => ({ status_code: 200, message: [] }),
    })),
  )
}

afterEach(() => vi.unstubAllGlobals())

describe('控制台骨架', () => {
  test('导航切换五个管理视图', async () => {
    stubFetch()
    const wrapper = mount(App)
    const navs = wrapper.findAll('.console__nav-item')
    expect(navs).toHaveLength(5)

    await wrapper.find('[data-test="nav-model"]').trigger('click')
    expect(wrapper.find('[data-test="model-table"]').exists()).toBe(true)

    await wrapper.find('[data-test="nav-skill"]').trigger('click')
    expect(wrapper.find('[data-test="skill-table"]').exists()).toBe(true)

    await wrapper.find('[data-test="nav-mcp"]').trigger('click')
    expect(wrapper.find('[data-test="mcp-table"]').exists()).toBe(true)

    await wrapper.find('[data-test="nav-tool"]').trigger('click')
    expect(wrapper.find('[data-test="tool-table"]').exists()).toBe(true)

    await wrapper.find('[data-test="nav-agent"]').trigger('click')
    expect(wrapper.find('[data-test="agent-table"]').exists()).toBe(true)
  })
})
