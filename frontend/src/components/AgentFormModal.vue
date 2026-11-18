<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { createAgent, updateAgent } from '@/api/agent'
import { listMcp } from '@/api/mcp'
import { listModels } from '@/api/model'
import { listSkills } from '@/api/skill'
import { listTools } from '@/api/tool'
import { showError } from '@/stores/app'
import OptionLabel from './OptionLabel.vue'
import type { AgentDetail, AgentPayload } from '@/types/agent'
import type { Id } from '@/types/common'
import type { McpItem } from '@/types/mcp'
import type { ModelItem } from '@/types/model'
import type { SkillItem } from '@/types/skill'
import type { ToolItem } from '@/types/tool'
import { iconTitle } from '@/utils/ui'

const props = defineProps<{ show: boolean; agent?: AgentDetail | null }>()
const emit = defineEmits<{ (e: 'update:show', value: boolean): void; (e: 'saved'): void }>()

const saving = ref(false)
const models = ref<ModelItem[]>([])
const tools = ref<ToolItem[]>([])
const skills = ref<SkillItem[]>([])
const mcps = ref<McpItem[]>([])

const form = reactive({
  name: '',
  description: '',
  soulPrompt: '',
  modelId: '' as Id,
  toolNames: [] as string[],
  skillIds: [] as Id[],
  mcpIds: [] as Id[],
})

// 表单内联校验提示（不再走全局 error alert）
const errors = reactive({ name: '', model: '' })

// chips 只显示名称，描述经 render-label 放进下拉项，避免长描述撑爆 tag
interface SelectOption {
  label: string
  value: string
  desc?: string
}

const modelOptions = computed(() =>
  models.value.map((m) => ({ label: `${m.name}（${m.model}）`, value: m.id })),
)
const toolOptions = computed<SelectOption[]>(() =>
  //load_skill 由框架自带，不参与装配（Tool 管理列表仍展示）
  tools.value
    .filter((t) => t.name !== 'load_skill')
    .map((t) => ({ label: t.name, value: t.name, desc: t.description })),
)
const skillOptions = computed<SelectOption[]>(() =>
  skills.value.map((s) => ({ label: s.name, value: s.id, desc: s.description })),
)
const mcpOptions = computed<SelectOption[]>(() =>
  mcps.value.map((m) => ({ label: m.name, value: m.id, desc: m.description || m.command || m.url || '' })),
)

watch(
  () => props.show,
  async (show) => {
    if (!show) return
    const [modelList, toolList, skillList, mcpList] = await Promise.all([
      listModels().catch(() => [] as ModelItem[]),
      listTools().catch(() => [] as ToolItem[]),
      listSkills().catch(() => [] as SkillItem[]),
      listMcp().catch(() => [] as McpItem[]),
    ])
    models.value = modelList
    tools.value = toolList
    skills.value = skillList
    mcps.value = mcpList
    fillForm()
  },
)

function fillForm(): void {
  const agent = props.agent
  form.name = agent?.name ?? ''
  form.description = agent?.description ?? ''
  form.soulPrompt = agent?.soul_prompt ?? ''
  form.modelId = agent ? String(agent.model_id) : ''
  form.toolNames = [...(agent?.tool_names ?? [])]
  form.skillIds = (agent?.skills ?? []).map((s) => String(s.id))
  form.mcpIds = (agent?.mcps ?? []).map((m) => String(m.id))
  errors.name = ''
  errors.model = ''
}

async function save(): Promise<void> {
  errors.name = form.name.trim() ? '' : '请填写 agent 名称'
  errors.model = form.modelId ? '' : '请选择模型'
  if (errors.name || errors.model) return
  saving.value = true
  const payload: AgentPayload = {
    name: form.name.trim(),
    description: form.description.trim(),
    soul_prompt: form.soulPrompt,
    model_id: String(form.modelId),
    tool_names: [...form.toolNames],
    skill_ids: form.skillIds.map(String),
    mcp_ids: form.mcpIds.map(String),
  }
  try {
    if (props.agent) {
      await updateAgent(String(props.agent.id), payload)
    } else {
      await createAgent(payload)
    }
    emit('update:show', false)
    emit('saved')
  } catch (e) {
    showError(e, '保存失败，请稍后重试')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <n-modal
    :show="props.show"
    preset="card"
    :title="iconTitle(props.agent ? 'fa-regular fa-pen-to-square' : 'fa-solid fa-plus', props.agent ? '编辑 agent' : '新建 agent')"
    class="agent-modal"
    @update:show="(value: boolean) => emit('update:show', value)"
  >
    <div class="form-stack">
      <n-input v-model:value="form.name" placeholder="名称" data-test="agent-form-name" />
      <div v-if="errors.name" class="field-error">{{ errors.name }}</div>
      <n-input
        v-model:value="form.description"
        type="textarea"
        placeholder="描述"
        :autosize="{ minRows: 2, maxRows: 4 }"
      />
      <div class="form-stack__label">角色提示词（追加在固定系统提示之后）</div>
      <n-input
        v-model:value="form.soulPrompt"
        type="textarea"
        placeholder="可留空"
        :autosize="{ minRows: 3, maxRows: 8 }"
        data-test="agent-form-soul"
      />
      <div class="form-stack__label">使用模型（单选）</div>
      <n-select
        v-model:value="form.modelId"
        :options="modelOptions"
        placeholder="选择模型"
        data-test="agent-form-model"
      />
      <div v-if="errors.model" class="field-error">{{ errors.model }}</div>
      <div class="form-stack__label">装配工具（多选）</div>
      <div class="form-hint">load_skill 由框架自带，无需装配</div>
      <n-select
        v-model:value="form.toolNames"
        multiple
        :options="toolOptions"
        placeholder="选择内置工具"
        data-test="agent-form-tools"
      >
        <template #render-label="{ option }">
          <OptionLabel :label="option.label" :desc="option.desc" />
        </template>
      </n-select>
      <div class="form-stack__label">装配 Skill（多选）</div>
      <n-select
        v-model:value="form.skillIds"
        multiple
        :options="skillOptions"
        placeholder="选择技能"
        data-test="agent-form-skills"
      >
        <template #render-label="{ option }">
          <OptionLabel :label="option.label" :desc="option.desc" />
        </template>
      </n-select>
      <div class="form-stack__label">装配 MCP（多选）</div>
      <n-select
        v-model:value="form.mcpIds"
        multiple
        :options="mcpOptions"
        placeholder="选择 MCP server"
        data-test="agent-form-mcps"
      >
        <template #render-label="{ option }">
          <OptionLabel :label="option.label" :desc="option.desc" />
        </template>
      </n-select>
    </div>
    <template #footer>
      <div class="form-actions">
        <n-button @click="emit('update:show', false)">取消</n-button>
        <n-button type="primary" :loading="saving" data-test="agent-form-save" @click="save">
          保存
        </n-button>
      </div>
    </template>
  </n-modal>
</template>
