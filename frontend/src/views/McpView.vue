<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { createMcp, deleteMcp, listMcp, updateMcp } from '@/api/mcp'
import EmptyState from '@/components/EmptyState.vue'
import { showError } from '@/stores/app'
import type { McpItem, McpPayload } from '@/types/mcp'
import { iconTitle } from '@/utils/ui'

const items = ref<McpItem[]>([])
const loading = ref(false)
const keyword = ref('')
const showForm = ref(false)
const showDetail = ref(false)
const saving = ref(false)
const editingId = ref('')
const detail = ref<McpItem | null>(null)

const form = reactive({ name: '', description: '', command: '', args: '', url: '' })
const errors = reactive({ name: '', pair: '' })
// args 未按 JSON 数组录入时按空白拆分兜底
const argsFallback = ref(false)

const filtered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return items.value
  return items.value.filter((it) =>
    [it.name, it.description, it.command, it.url].some((f) => f.toLowerCase().includes(kw)),
  )
})

const emptyText = computed(() => (keyword.value.trim() ? '无匹配结果' : '暂无 MCP server'))

onMounted(() => void reload())

async function reload(): Promise<void> {
  loading.value = true
  try {
    items.value = await listMcp()
  } catch (e) {
    showError(e, '加载 MCP 列表失败')
  } finally {
    loading.value = false
  }
}

function openCreate(): void {
  editingId.value = ''
  Object.assign(form, { name: '', description: '', command: '', args: '', url: '' })
  errors.name = ''
  errors.pair = ''
  argsFallback.value = false
  showForm.value = true
}

function openEdit(item: McpItem): void {
  editingId.value = String(item.id)
  Object.assign(form, {
    name: item.name,
    description: item.description,
    command: item.command,
    // args 用 JSON 数组回填，含空格参数不丢义
    args: JSON.stringify(item.args),
    url: item.url,
  })
  errors.name = ''
  errors.pair = ''
  argsFallback.value = false
  showForm.value = true
}

function openDetail(item: McpItem): void {
  detail.value = item
  showDetail.value = true
}

// 优先 JSON 数组解析；非法 JSON 回落按空白拆分
function parseArgs(raw: string): string[] {
  const text = raw.trim()
  if (!text) {
    argsFallback.value = false
    return []
  }
  try {
    const parsed: unknown = JSON.parse(text)
    if (Array.isArray(parsed)) {
      argsFallback.value = false
      return parsed.map(String)
    }
    argsFallback.value = true
    return text.split(/\s+/)
  } catch {
    argsFallback.value = true
    return text.split(/\s+/)
  }
}

async function save(): Promise<void> {
  errors.name = form.name.trim() ? '' : '请填写 MCP server 名称'
  errors.pair = !form.command.trim() && !form.url.trim() ? '请填写 command 或 url（二选一）' : ''
  if (errors.name || errors.pair) return
  saving.value = true
  try {
    const payload: McpPayload = {
      name: form.name.trim(),
      description: form.description.trim(),
      command: form.command.trim(),
      args: parseArgs(form.args),
      url: form.url.trim(),
    }
    if (editingId.value) {
      await updateMcp(editingId.value, payload)
    } else {
      await createMcp(payload)
    }
    showForm.value = false
    await reload()
  } catch (e) {
    showError(e, '保存失败，请稍后重试')
  } finally {
    saving.value = false
  }
}

async function remove(item: McpItem): Promise<void> {
  try {
    await deleteMcp(String(item.id))
    await reload()
  } catch (e) {
    showError(e, '删除失败，请稍后重试')
  }
}
</script>

<template>
  <section class="view">
    <header class="view__header">
      <span class="view__title">MCP 管理</span>
      <div class="view__actions">
        <n-button circle quaternary title="刷新" @click="reload">
          <i class="fa-solid fa-rotate" />
        </n-button>
        <n-button type="primary" data-test="mcp-create" @click="openCreate">
          <i class="fa-solid fa-plus" />&nbsp;新建 MCP server
        </n-button>
      </div>
    </header>

    <div class="panel">
      <div class="panel__toolbar">
        <n-input v-model:value="keyword" class="search-box" placeholder="搜索名称 / 描述 / command / url" clearable>
          <template #prefix><i class="fa-solid fa-magnifying-glass" /></template>
        </n-input>
      </div>
      <n-spin :show="loading">
        <table class="table" data-test="mcp-table">
          <thead>
            <tr>
              <th>名称</th>
              <th>描述</th>
              <th>接入方式</th>
              <th>更新时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filtered" :key="item.id">
              <td>{{ item.name }}</td>
              <td>{{ item.description || '—' }}</td>
              <td>{{ item.command ? 'command' : 'url' }}</td>
              <td>{{ item.updated_at }}</td>
              <td class="table__actions">
                <n-button size="small" circle quaternary title="详情" data-test="mcp-detail" @click="openDetail(item)">
                  <i class="fa-regular fa-eye" />
                </n-button>
                <n-button size="small" circle quaternary title="编辑" @click="openEdit(item)">
                  <i class="fa-regular fa-pen-to-square" />
                </n-button>
                <n-popconfirm @positive-click="remove(item)">
                  <template #trigger>
                    <n-button size="small" circle quaternary type="error" title="删除">
                      <i class="fa-regular fa-trash-can" />
                    </n-button>
                  </template>
                  确认删除 MCP server「{{ item.name }}」？
                </n-popconfirm>
              </td>
            </tr>
            <tr v-if="!loading && filtered.length === 0">
              <td colspan="5" class="table__empty">
                <EmptyState icon="fa-solid fa-inbox" :text="emptyText" />
              </td>
            </tr>
          </tbody>
        </table>
      </n-spin>
    </div>

    <n-modal v-model:show="showDetail" preset="card" :title="iconTitle('fa-solid fa-plug', 'MCP server 详情')" class="agent-modal">
      <div class="form-stack" data-test="mcp-detail-body">
        <div class="form-stack__label">名称</div>
        <div>{{ detail?.name }}</div>
        <div class="form-stack__label">描述</div>
        <div>{{ detail?.description || '—' }}</div>
        <div class="form-stack__label">command</div>
        <div class="table__mono">{{ detail?.command || '—' }}</div>
        <div class="form-stack__label">args</div>
        <div class="table__mono">{{ detail?.args.join(' ') || '—' }}</div>
        <div class="form-stack__label">url</div>
        <div class="table__mono">{{ detail?.url || '—' }}</div>
        <div class="form-stack__label">更新时间</div>
        <div>{{ detail?.updated_at }}</div>
      </div>
    </n-modal>

    <n-modal
      v-model:show="showForm"
      preset="card"
      :title="iconTitle(editingId ? 'fa-regular fa-pen-to-square' : 'fa-solid fa-plus', editingId ? '编辑 MCP server' : '新建 MCP server')"
      class="agent-modal"
    >
      <div class="form-stack">
        <n-input v-model:value="form.name" placeholder="名称（唯一）" data-test="mcp-name" />
        <div v-if="errors.name" class="field-error">{{ errors.name }}</div>
        <n-input
          v-model:value="form.description"
          type="textarea"
          placeholder="描述"
          :autosize="{ minRows: 2, maxRows: 4 }"
        />
        <n-input v-model:value="form.command" placeholder="command（stdio 方式）" data-test="mcp-command" />
        <n-input v-model:value="form.args" placeholder='args（JSON 数组，如 ["-y","xxx"]）' />
        <div v-if="argsFallback" class="field-error">未识别为 JSON 数组，已按空格拆分</div>
        <div class="form-hint">args 填 JSON 数组（含空格的参数不会被拆坏）；非数组内容将按空格拆分</div>
        <n-input
          v-model:value="form.url"
          placeholder="url（http 方式）"
          data-test="mcp-url"
        />
        <div class="form-hint">command（stdio）与 url（http）二选一；两项都填时 command 优先</div>
        <div v-if="errors.pair" class="field-error">{{ errors.pair }}</div>
      </div>
      <template #footer>
        <div class="form-actions">
          <n-button @click="showForm = false">取消</n-button>
          <n-button type="primary" :loading="saving" data-test="mcp-save" @click="save">保存</n-button>
        </div>
      </template>
    </n-modal>
  </section>
</template>
