<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { listTools } from '@/api/tool'
import EmptyState from '@/components/EmptyState.vue'
import { showError } from '@/stores/app'
import type { ToolItem } from '@/types/tool'
import { iconTitle } from '@/utils/ui'

const items = ref<ToolItem[]>([])
const loading = ref(false)
const keyword = ref('')
const showDetail = ref(false)
const detail = ref<ToolItem | null>(null)

const filtered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return items.value
  return items.value.filter((it) =>
    [it.name, it.description].some((f) => f.toLowerCase().includes(kw)),
  )
})

const emptyText = computed(() => (keyword.value.trim() ? '无匹配结果' : '暂无内置工具'))

onMounted(() => void reload())

async function reload(): Promise<void> {
  loading.value = true
  try {
    items.value = await listTools()
  } catch (e) {
    showError(e, '加载工具列表失败')
  } finally {
    loading.value = false
  }
}

function openDetail(item: ToolItem): void {
  detail.value = item
  showDetail.value = true
}

function prettyParams(item: ToolItem | null): string {
  return item ? JSON.stringify(item.parameters, null, 2) : ''
}
</script>

<template>
  <section class="view">
    <header class="view__header">
      <span class="view__title">Tool 管理（内置，只读）</span>
      <div class="view__actions">
        <n-button circle quaternary title="刷新" @click="reload">
          <i class="fa-solid fa-rotate" />
        </n-button>
      </div>
    </header>

    <div class="panel">
      <div class="panel__toolbar">
        <n-input v-model:value="keyword" class="search-box" placeholder="搜索工具名称 / 描述" clearable>
          <template #prefix><i class="fa-solid fa-magnifying-glass" /></template>
        </n-input>
      </div>
      <n-spin :show="loading">
        <table class="table" data-test="tool-table">
          <thead>
            <tr>
              <th>工具名称</th>
              <th>描述</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filtered" :key="item.name">
              <td class="table__mono">{{ item.name }}</td>
              <td>{{ item.description }}</td>
              <td class="table__actions">
                <n-button size="small" circle quaternary title="详情" data-test="tool-detail" @click="openDetail(item)">
                  <i class="fa-regular fa-eye" />
                </n-button>
              </td>
            </tr>
            <tr v-if="!loading && filtered.length === 0">
              <td colspan="3" class="table__empty">
                <EmptyState icon="fa-solid fa-inbox" :text="emptyText" />
              </td>
            </tr>
          </tbody>
        </table>
      </n-spin>
    </div>

    <n-modal v-model:show="showDetail" preset="card" :title="iconTitle('fa-solid fa-screwdriver-wrench', '工具详情')" class="agent-modal">
      <div class="form-stack" data-test="tool-detail-body">
        <div class="form-stack__label">名称</div>
        <div class="table__mono">{{ detail?.name }}</div>
        <div class="form-stack__label">描述</div>
        <div>{{ detail?.description }}</div>
        <div class="form-stack__label">参数 schema</div>
        <pre class="detail-pre">{{ prettyParams(detail) }}</pre>
      </div>
    </n-modal>
  </section>
</template>
