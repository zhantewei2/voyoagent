<script setup lang="ts">
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'

const props = defineProps<{ content: string }>()

// html: false 防注入
const md = new MarkdownIt({ html: false, breaks: true, linkify: true })
const html = computed(() => md.render(props.content))
</script>

<template>
  <div class="markdown-content" data-test="markdown-content" v-html="html" />
</template>
