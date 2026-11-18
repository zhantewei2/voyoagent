import { config } from '@vue/test-utils'

// jsdom 环境补齐 storage（方法层测试主要走 store，无需 UI 插件）
await import('jsdom').then(({ JSDOM }) => {
  const dom = new JSDOM('', { url: 'http://localhost' })
  ;(globalThis as any).localStorage = dom.window.localStorage
  ;(globalThis as any).sessionStorage = dom.window.sessionStorage
})

config.global.config.warnHandler = () => {}
