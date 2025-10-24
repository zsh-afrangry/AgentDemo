<template>
  <div>
    <h3>分析结果</h3>
    <p v-if="loading" class="muted">正在分析，请稍候…</p>
    <p v-else-if="!hasData" class="muted">暂无结果。</p>

    <div v-if="hasData" style="display:flex; flex-direction:column; gap:16px; margin-top:8px;">
      <div
        v-for="(info, agent) in resultsByAgent"
        :key="agent"
        class="agent-block"
        :class="info.status === 'success' ? 'ok' : 'err'"
      >
        <header style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
          <span class="badge" :class="info.status === 'success' ? 'tag-ok' : 'tag-err'">
            {{ prettyName(agent) }}
          </span>
          <span v-if="info.status==='success'">生成问题数：{{ (info.questions || []).length }}</span>
          <span v-else class="muted">失败：{{ info.error || '未知错误' }}</span>
        </header>

        <table v-if="info.status==='success' && (info.questions || []).length" class="table">
          <thead>
            <tr><th style="width:60px;">ID</th><th>问题描述</th></tr>
          </thead>
          <tbody>
            <tr v-for="q in info.questions" :key="q.id">
              <td><span class="code">{{ q.id }}</span></td>
              <td>{{ q.description }}</td>
            </tr>
          </tbody>
        </table>

        <details v-else-if="info.status==='failed' && info.raw_output">
          <summary class="muted">查看原始输出</summary>
          <pre style="white-space: pre-wrap; margin:6px 0 0 0;">{{ info.raw_output }}</pre>
        </details>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  loading: { type: Boolean, default: false },
  resultsByAgent: { type: Object, default: () => ({}) }
})

const hasData = computed(() => Object.keys(props.resultsByAgent || {}).length > 0)

function prettyName(key) {
  const map = {
    aggregate: '聚合/网络异常（aggregate）',
    binary: '状态矛盾（binary）',
    process: '流程/资格矛盾（process）',
    quantitative: '数值会计不一致（quantitative）',
    temporal: '时间/因果矛盾（temporal）',
  }
  return map[key] || key
}
</script>

<style scoped>
.agent-block { border:1px dashed var(--border); border-radius: 10px; padding: 10px; }
.agent-block.ok { border-color:#bae6fd; background:#f0f9ff; }
.agent-block.err { border-color:#fecaca; background:#fef2f2; }
</style>
