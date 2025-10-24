<template>
  <div>
    <h3>运行日志</h3>
    <div class="box">
      <div v-for="(line, i) in logs" :key="i" class="line">{{ line }}</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  logs: { type: Array, default: () => [] }
})
</script>

<style scoped>
.box {
  margin-top: 6px;
  background:#f8f9fb;
  border:1px solid var(--border);
  border-radius: 10px;
  padding:8px;
  max-height: 340px;
  overflow:auto;
}
.line {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size:12px;
  border-bottom:1px dashed var(--border);
  padding:4px 0;
}
.line:last-child { border-bottom: none; }
</style>
