<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { createModel, deleteModel, listModels, updateModel } from '@/api/model'
import EmptyState from '@/components/EmptyState.vue'
import { showError } from '@/stores/app'
import type { ModelItem, ModelPayload } from '@/types/model'
import { iconTitle } from '@/utils/ui'

const items = ref<ModelItem[]>([])
const loading = ref(false)
const keyword = ref('')
const showForm = ref(false)
const showDetail = ref(false)
const saving = ref(false)
const editingId = ref('')
const detail = ref<ModelItem | null>(null)

const form = reactive<ModelPayload>({
  name: '',
  model: '',
  base_url: '',
  api_key: '',
  description: '',
})

// 表单内联校验提示（不再走全局 error alert）
const errors = reactive({ name: '', model: '', base_url: '', api_key: '' })

const filtered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return items.value
  return items.value.filter((it) =>
    [it.name, it.model, it.base_url, it.description].some((f) => f.toLowerCase().includes(kw)),
  )
})

const emptyText = computed(() => (keyword.value.trim() ? '无匹配结果' : '暂无模型'))

onMounted(() => void reload())

async function reload(): Promise<void> {
  loading.value = true
  try {
    items.value = await listModels()
  } catch (e) {
    showError(e, '加载模型列表失败')
  } finally {
    loading.value = false
  }
}

function clearErrors(): void {
  errors.name = ''
  errors.model = ''
  errors.base_url = ''
  errors.api_key = ''
}

function openCreate(): void {
  editingId.value = ''
  Object.assign(form, { name: '', model: '', base_url: '', api_key: '', description: '' })
  clearErrors()
  showForm.value = true
}

function openEdit(item: ModelItem): void {
  editingId.value = String(item.id)
  // api_key 为脱敏值：留空表示不修改
  Object.assign(form, {
    name: item.name,
    model: item.model,
    base_url: item.base_url,
    api_key: '',
    description: item.description,
  })
  clearErrors()
  showForm.value = true
}

function openDetail(item: ModelItem): void {
  detail.value = item
  showDetail.value = true
}

function validate(): boolean {
  errors.name = form.name.trim() ? '' : '请填写名称'
  errors.model = form.model.trim() ? '' : '请填写 model'
  errors.base_url = form.base_url.trim() ? '' : '请填写 base_url'
  errors.api_key = !editingId.value && !form.api_key.trim() ? '请填写 api_key' : ''
  return !errors.name && !errors.model && !errors.base_url && !errors.api_key
}

async function save(): Promise<void> {
  if (!validate()) return
  saving.value = true
  try {
    const payload: ModelPayload = {
      name: form.name.trim(),
      model: form.model.trim(),
      base_url: form.base_url.trim(),
      api_key: form.api_key.trim(),
      description: form.description.trim(),
    }
    if (editingId.value) {
      await updateModel(editingId.value, payload)
    } else {
      await createModel(payload)
    }
    showForm.value = false
    await reload()
  } catch (e) {
    showError(e, '保存失败，请稍后重试')
  } finally {
    saving.value = false
  }
}

async function remove(item: ModelItem): Promise<void> {
  try {
    await deleteModel(String(item.id))
    await reload()
  } catch (e) {
    showError(e, '删除失败，请稍后重试')
  }
}
</script>

<template>
  <section class="view">
    <header class="view__header">
      <span class="view__title">模型管理</span>
      <div class="view__actions">
        <n-button circle quaternary title="刷新" @click="reload">
          <i class="fa-solid fa-rotate" />
        </n-button>
        <n-button type="primary" data-test="model-create" @click="openCreate">
          <i class="fa-solid fa-plus" />&nbsp;新建模型
        </n-button>
      </div>
    </header>

    <div class="panel">
      <div class="panel__toolbar">
        <n-input v-model:value="keyword" class="search-box" placeholder="搜索名称 / model / base_url" clearable>
          <template #prefix><i class="fa-solid fa-magnifying-glass" /></template>
        </n-input>
      </div>
      <n-spin :show="loading">
        <table class="table" data-test="model-table">
          <thead>
            <tr>
              <th>名称</th>
              <th>model</th>
              <th>base_url</th>
              <th>备注</th>
              <th>更新时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filtered" :key="item.id">
              <td>{{ item.name }}</td>
              <td class="table__mono">{{ item.model }}</td>
              <td class="table__mono">{{ item.base_url }}</td>
              <td>{{ item.description || '—' }}</td>
              <td>{{ item.updated_at }}</td>
              <td class="table__actions">
                <n-button size="small" circle quaternary title="详情" data-test="model-detail" @click="openDetail(item)">
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
                  确认删除模型「{{ item.name }}」？
                </n-popconfirm>
              </td>
            </tr>
            <tr v-if="!loading && filtered.length === 0">
              <td colspan="6" class="table__empty">
                <EmptyState icon="fa-solid fa-inbox" :text="emptyText" />
              </td>
            </tr>
          </tbody>
        </table>
      </n-spin>
    </div>

    <n-modal v-model:show="showDetail" preset="card" :title="iconTitle('fa-solid fa-cube', '模型详情')" class="agent-modal">
      <div class="form-stack" data-test="model-detail-body">
        <div class="form-stack__label">名称</div>
        <div>{{ detail?.name }}</div>
        <div class="form-stack__label">model</div>
        <div class="table__mono">{{ detail?.model }}</div>
        <div class="form-stack__label">base_url</div>
        <div class="table__mono">{{ detail?.base_url }}</div>
        <div class="form-stack__label">api_key（脱敏）</div>
        <div class="table__mono">{{ detail?.api_key }}</div>
        <div class="form-stack__label">备注</div>
        <div>{{ detail?.description || '—' }}</div>
        <div class="form-stack__label">更新时间</div>
        <div>{{ detail?.updated_at }}</div>
      </div>
    </n-modal>

    <n-modal
      v-model:show="showForm"
      preset="card"
      :title="iconTitle(editingId ? 'fa-regular fa-pen-to-square' : 'fa-solid fa-plus', editingId ? '编辑模型' : '新建模型')"
      class="agent-modal"
    >
      <div class="form-stack">
        <div class="form-hint">本系统通过 OpenAI Responses API 兼容接口调用模型（不支持 Anthropic 接口）</div>
        <n-input v-model:value="form.name" placeholder="名称（唯一）" data-test="model-name" />
        <div v-if="errors.name" class="field-error">{{ errors.name }}</div>
        <n-input v-model:value="form.model" placeholder="model" />
        <div class="form-hint">须与 base_url 服务提供的模型 id 一致</div>
        <div v-if="errors.model" class="field-error">{{ errors.model }}</div>
        <n-input v-model:value="form.base_url" placeholder="base_url，如 https://api.longcat.chat/openai/v1" />
        <div v-if="errors.base_url" class="field-error">{{ errors.base_url }}</div>
        <n-input
          v-model:value="form.api_key"
          type="password"
          show-password-on="click"
          :placeholder="editingId ? '留空则保持原 api_key 不变' : 'api_key'"
          data-test="model-api-key"
        />
        <div v-if="errors.api_key" class="field-error">{{ errors.api_key }}</div>
        <n-input
          v-model:value="form.description"
          type="textarea"
          placeholder="备注"
          :autosize="{ minRows: 2, maxRows: 4 }"
        />
      </div>
      <template #footer>
        <div class="form-actions">
          <n-button @click="showForm = false">取消</n-button>
          <n-button type="primary" :loading="saving" data-test="model-save" @click="save">保存</n-button>
        </div>
      </template>
    </n-modal>
  </section>
</template>
