<template>
  <div>
    <div class="muted" style="margin-bottom:6px;">可选择一个或多个：</div>
    <div style="display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap:6px;">
      <label v-for="opt in options" :key="opt.value" class="badge" style="cursor:pointer;">
        <input
          type="checkbox"
          :value="opt.value"
          :checked="isChecked(opt.value)"
          @change="toggle(opt.value, $event.target.checked)"
          :disabled="loading"
          style="margin-right:6px"
        />
        <span>{{ opt.label }}</span>
      </label>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  selectedAgents: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
})
const emit = defineEmits(['update:selected-agents'])

const options = [
  { value: 'aggregate',    label: '聚合/网络异常（aggregate）' },
  { value: 'binary',       label: '状态矛盾（binary）' },
  { value: 'process',      label: '流程/资格矛盾（process）' },
  { value: 'quantitative', label: '数值会计不一致（quantitative）' },
  { value: 'temporal',     label: '时间/因果矛盾（temporal）' },
]

function isChecked(val) {
  return props.selectedAgents.includes(val)
}

function toggle(val, checked) {
  const next = checked
    ? Array.from(new Set([...props.selectedAgents, val]))
    : props.selectedAgents.filter(x => x !== val)
  emit('update:selected-agents', next)
}
</script>
