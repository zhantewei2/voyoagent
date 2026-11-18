<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { deleteAgent, getAgent, listAgents } from '@/api/agent'
import AgentFormModal from '@/components/AgentFormModal.vue'
import EmptyState from '@/components/EmptyState.vue'
import { openAgentDetail, showError } from '@/stores/app'
import type { AgentDetail, AgentItem } from '@/types/agent'

const items = ref<AgentItem[]>([])
const loading = ref(false)
const keyword = ref('')
const showForm = ref(false)
const editing = ref<AgentDetail | null>(null)

const filtered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return items.value
  return items.value.filter((it) =>
    [it.name, it.description, it.model_name].some((f) => (f ?? '').toLowerCase().includes(kw)),
  )
})

const emptyText = computed(() => (keyword.value.trim() ? '无匹配结果' : '暂无 agent'))

onMounted(() => void reload())

async function reload(): Promise<void> {
  loading.value = true
  try {
    items.value = await listAgents()
  } catch (e) {
    showError(e, '加载 agent 列表失败')
  } finally {
    loading.value = false
  }
}

function openCreate(): void {
  editing.value = null
  showForm.value = true
}

//编辑复用详情数据（含装配 id），保证表单选项回填准确
async function openEdit(item: AgentItem): Promise<void> {
  try {
    editing.value = await getAgent(String(item.id))
    showForm.value = true
  } catch (e) {
    showError(e, '读取 agent 详情失败')
  }
}

async function remove(item: AgentItem): Promise<void> {
  try {
    await deleteAgent(String(item.id))
    await reload()
  } catch (e) {
    showError(e, '删除失败，请稍后重试')
  }
}
</script>

<template>
  <section class="view">
    <header class="view__header">
      <span class="view__title">Agent 管理</span>
      <div class="view__actions">
        <n-button circle quaternary title="刷新" @click="reload">
          <i class="fa-solid fa-rotate" />
        </n-button>
        <n-button type="primary" data-test="agent-create" @click="openCreate">
          <i class="fa-solid fa-plus" />&nbsp;新建 agent
        </n-button>
      </div>
    </header>

    <div class="panel">
      <div class="panel__toolbar">
        <n-input v-model:value="keyword" class="search-box" placeholder="搜索名称 / 描述 / 模型" clearable>
          <template #prefix><i class="fa-solid fa-magnifying-glass" /></template>
        </n-input>
      </div>
      <n-spin :show="loading">
        <table class="table" data-test="agent-table">
          <thead>
            <tr>
              <th>名称</th>
              <th>描述</th>
              <th>使用模型</th>
              <th>工具</th>
              <th>MCP</th>
              <th>技能</th>
              <th>更新时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in filtered"
              :key="item.id"
              class="table__row"
              data-test="agent-row"
              @click="openAgentDetail(item.id)"
            >
              <td>{{ item.name }}</td>
              <td>{{ item.description || '—' }}</td>
              <td>{{ item.model_name || '—' }}</td>
              <td>{{ item.tool_names.join('、') || '—' }}</td>
              <td>{{ item.mcp_names.join('、') || '—' }}</td>
              <td>{{ item.skill_names.join('、') || '—' }}</td>
              <td>{{ item.updated_at }}</td>
              <td class="table__actions" @click.stop>
                <n-button size="small" circle quaternary title="详情调试" data-test="agent-open" @click="openAgentDetail(item.id)">
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
                  确认删除 agent「{{ item.name }}」？
                </n-popconfirm>
              </td>
            </tr>
            <tr v-if="!loading && filtered.length === 0">
              <td colspan="8" class="table__empty">
                <EmptyState icon="fa-solid fa-inbox" :text="emptyText" />
              </td>
            </tr>
          </tbody>
        </table>
      </n-spin>
    </div>

    <AgentFormModal v-model:show="showForm" :agent="editing" @saved="reload" />
  </section>
</template>
