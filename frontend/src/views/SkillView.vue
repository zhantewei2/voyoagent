<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { createSkill, deleteSkill, getSkill, listSkills, updateSkill } from '@/api/skill'
import EmptyState from '@/components/EmptyState.vue'
import { showError } from '@/stores/app'
import type { SkillDetail, SkillItem, SkillPayload } from '@/types/skill'
import { iconTitle } from '@/utils/ui'

// content 为带 frontmatter 的 markdown，占位符给出模板避免误填
const CONTENT_PLACEHOLDER = `---
name: skill-name
description: 一句话描述
---
（markdown 正文）`

const items = ref<SkillItem[]>([])
const loading = ref(false)
const keyword = ref('')
const showForm = ref(false)
const showDetail = ref(false)
const saving = ref(false)
const editingId = ref('')
const detail = ref<SkillDetail | null>(null)

const form = reactive<SkillPayload>({ name: '', description: '', content: '' })
const errors = reactive({ name: '' })

const filtered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return items.value
  return items.value.filter((it) =>
    [it.name, it.description].some((f) => f.toLowerCase().includes(kw)),
  )
})

const emptyText = computed(() => (keyword.value.trim() ? '无匹配结果' : '暂无技能'))

onMounted(() => void reload())

async function reload(): Promise<void> {
  loading.value = true
  try {
    items.value = await listSkills()
  } catch (e) {
    showError(e, '加载技能列表失败')
  } finally {
    loading.value = false
  }
}

function openCreate(): void {
  editingId.value = ''
  Object.assign(form, { name: '', description: '', content: '' })
  errors.name = ''
  showForm.value = true
}

async function openEdit(item: SkillItem): Promise<void> {
  try {
    const full = await getSkill(String(item.id))
    editingId.value = String(item.id)
    Object.assign(form, { name: full.name, description: full.description, content: full.content })
    errors.name = ''
    showForm.value = true
  } catch (e) {
    showError(e, '读取技能详情失败')
  }
}

async function openDetail(item: SkillItem): Promise<void> {
  try {
    detail.value = await getSkill(String(item.id))
    showDetail.value = true
  } catch (e) {
    showError(e, '读取技能详情失败')
  }
}

async function save(): Promise<void> {
  errors.name = form.name.trim() ? '' : '请填写技能名称'
  if (errors.name) return
  saving.value = true
  try {
    const payload: SkillPayload = {
      name: form.name.trim(),
      description: form.description.trim(),
      content: form.content,
    }
    if (editingId.value) {
      await updateSkill(editingId.value, payload)
    } else {
      await createSkill(payload)
    }
    showForm.value = false
    await reload()
  } catch (e) {
    showError(e, '保存失败，请稍后重试')
  } finally {
    saving.value = false
  }
}

async function remove(item: SkillItem): Promise<void> {
  try {
    await deleteSkill(String(item.id))
    await reload()
  } catch (e) {
    showError(e, '删除失败，请稍后重试')
  }
}
</script>

<template>
  <section class="view">
    <header class="view__header">
      <span class="view__title">Skill 管理</span>
      <div class="view__actions">
        <n-button circle quaternary title="刷新" @click="reload">
          <i class="fa-solid fa-rotate" />
        </n-button>
        <n-button type="primary" data-test="skill-create" @click="openCreate">
          <i class="fa-solid fa-plus" />&nbsp;新建技能
        </n-button>
      </div>
    </header>

    <div class="panel">
      <div class="panel__toolbar">
        <n-input v-model:value="keyword" class="search-box" placeholder="搜索名称 / 描述" clearable>
          <template #prefix><i class="fa-solid fa-magnifying-glass" /></template>
        </n-input>
      </div>
      <n-spin :show="loading">
        <table class="table" data-test="skill-table">
          <thead>
            <tr>
              <th>名称</th>
              <th>描述</th>
              <th>更新时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filtered" :key="item.id">
              <td>{{ item.name }}</td>
              <td>{{ item.description || '—' }}</td>
              <td>{{ item.updated_at }}</td>
              <td class="table__actions">
                <n-button size="small" circle quaternary title="详情" data-test="skill-detail" @click="openDetail(item)">
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
                  确认删除技能「{{ item.name }}」？
                </n-popconfirm>
              </td>
            </tr>
            <tr v-if="!loading && filtered.length === 0">
              <td colspan="4" class="table__empty">
                <EmptyState icon="fa-solid fa-inbox" :text="emptyText" />
              </td>
            </tr>
          </tbody>
        </table>
      </n-spin>
    </div>

    <n-modal v-model:show="showDetail" preset="card" :title="iconTitle('fa-solid fa-wand-magic-sparkles', '技能详情')" class="agent-modal">
      <div class="form-stack" data-test="skill-detail-body">
        <div class="form-stack__label">名称</div>
        <div>{{ detail?.name }}</div>
        <div class="form-stack__label">描述</div>
        <div>{{ detail?.description || '—' }}</div>
        <div class="form-stack__label">技能正文</div>
        <pre class="detail-pre">{{ detail?.content }}</pre>
        <div class="form-stack__label">更新时间</div>
        <div>{{ detail?.updated_at }}</div>
      </div>
    </n-modal>

    <n-modal
      v-model:show="showForm"
      preset="card"
      :title="iconTitle(editingId ? 'fa-regular fa-pen-to-square' : 'fa-solid fa-plus', editingId ? '编辑技能' : '新建技能')"
      class="agent-modal"
    >
      <div class="form-stack">
        <n-input v-model:value="form.name" placeholder="名称（唯一）" data-test="skill-name" />
        <div v-if="errors.name" class="field-error">{{ errors.name }}</div>
        <n-input
          v-model:value="form.description"
          type="textarea"
          placeholder="描述"
          :autosize="{ minRows: 2, maxRows: 4 }"
        />
        <div class="form-stack__label">技能正文（markdown，含 frontmatter）</div>
        <n-input
          v-model:value="form.content"
          type="textarea"
          :placeholder="CONTENT_PLACEHOLDER"
          :autosize="{ minRows: 10, maxRows: 20 }"
          data-test="skill-content"
        />
      </div>
      <template #footer>
        <div class="form-actions">
          <n-button @click="showForm = false">取消</n-button>
          <n-button type="primary" :loading="saving" data-test="skill-save" @click="save">保存</n-button>
        </div>
      </template>
    </n-modal>
  </section>
</template>
