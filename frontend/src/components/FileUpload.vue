<template>
  <div>
    <input
      class="input"
      type="file"
      accept=".sql,text/sql"
      @change="onChange"
    />
    <p class="muted" style="margin-top:8px">仅需上传 Schema（包含注释的 SQL）。</p>
  </div>
</template>

<script setup>
const emit = defineEmits(['file-selected'])

function onChange(e) {
  const file = e.target.files?.[0]
  if (file) emit('file-selected', file)
}
</script>
