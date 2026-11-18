import { h, type VNodeChild } from 'vue'

// modal 标题统一「图标 + 文字」
export function iconTitle(icon: string, text: string): () => VNodeChild {
  return () => h('span', { class: 'modal-title' }, [h('i', { class: icon }), text])
}
