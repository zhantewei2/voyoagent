<script setup lang="ts">
import { state as appState, setView, type ViewKey } from '@/stores/app'
import AgentDetailView from '@/views/AgentDetailView.vue'
import AgentView from '@/views/AgentView.vue'
import McpView from '@/views/McpView.vue'
import ModelView from '@/views/ModelView.vue'
import SkillView from '@/views/SkillView.vue'
import ToolView from '@/views/ToolView.vue'

// Naive UI 会计算颜色，必须使用与 vars.scss 令牌一致的静态色值
const themeOverrides = {
  common: {
    primaryColor: '#00716c',
    primaryColorHover: '#00847e',
    primaryColorPressed: '#005e5a',
    primaryColorSuppl: '#00847e',
    borderRadius: 'var(--radius-md)',
    textColorBase: '#132528',
    textColor1: '#132528',
    textColor2: '#45595d',
  },
  Button: {
    borderRadiusSmall: 'var(--radius-md)',
    borderRadiusMedium: 'var(--radius-md)',
    borderRadiusLarge: 'var(--radius-md)',
  },
  Card: { borderRadius: 'var(--radius-card)' },
}

const NAV_GROUPS: { label: string; items: { key: ViewKey; label: string; icon: string }[] }[] = [
  {
    label: '资产管理',
    items: [
      { key: 'model', label: '模型管理', icon: 'fa-solid fa-cube' },
      { key: 'skill', label: 'Skill 管理', icon: 'fa-solid fa-wand-magic-sparkles' },
      { key: 'mcp', label: 'MCP 管理', icon: 'fa-solid fa-plug' },
      { key: 'tool', label: 'Tool 管理', icon: 'fa-solid fa-screwdriver-wrench' },
    ],
  },
  {
    label: 'Agent',
    items: [{ key: 'agent', label: 'Agent 管理', icon: 'fa-solid fa-robot' }],
  },
]
</script>

<template>
  <n-config-provider :theme-overrides="themeOverrides">
    <div class="console">
      <header class="console__topbar">
        <div class="console__brand">
          <span class="console__logo"><i class="fa-solid fa-robot" /></span>
          Agent 管理平台
        </div>
      </header>

      <div class="console__body">
        <aside class="console__nav">
          <template v-for="group in NAV_GROUPS" :key="group.label">
            <div class="console__group-label">{{ group.label }}</div>
            <button
              v-for="item in group.items"
              :key="item.key"
              class="console__nav-item"
              :class="{ 'is-active': appState.activeView === item.key }"
              :data-test="`nav-${item.key}`"
              @click="setView(item.key)"
            >
              <i :class="item.icon" />
              {{ item.label }}
            </button>
          </template>
        </aside>

        <main class="console__main">
          <div class="console__inner">
            <n-alert
              v-if="appState.errorMsg"
              type="error"
              closable
              class="console__error"
              data-test="console-error"
              @close="appState.errorMsg = ''"
            >
              {{ appState.errorMsg }}
            </n-alert>
            <ModelView v-if="appState.activeView === 'model'" />
            <SkillView v-else-if="appState.activeView === 'skill'" />
            <McpView v-else-if="appState.activeView === 'mcp'" />
            <ToolView v-else-if="appState.activeView === 'tool'" />
            <AgentDetailView v-else-if="appState.activeView === 'agentDetail'" />
            <AgentView v-else />
          </div>
        </main>
      </div>
    </div>
  </n-config-provider>
</template>
