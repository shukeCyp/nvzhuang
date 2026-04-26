<template>
  <div class="select-wrap">
    <select :value="selectedIndex" @change="onChange">
      <option v-for="(opt, index) in options" :key="String(opt.value)" :value="index">{{ opt.label }}</option>
    </select>
    <span class="select-arrow">›</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number, Boolean, Object, Array],
    default: '',
  },
  options: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['update:modelValue'])

const selectedIndex = computed(() => {
  const index = props.options.findIndex((opt) => Object.is(opt.value, props.modelValue))
  return index >= 0 ? String(index) : '0'
})

function onChange(event) {
  const index = Number(event.target.value)
  const option = props.options[index]
  emit('update:modelValue', option ? option.value : '')
}
</script>

<style scoped>
.select-wrap { position: relative; display: inline-flex; width: 100%; }
select {
  width: 100%; padding: 8px 32px 8px 12px; border: 1px solid #e0e0e0;
  border-radius: 8px; font-size: 13px; color: #1a1a1a; background: #fff;
  appearance: none; outline: none; cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
}
select:hover { border-color: #c0c0c0; }
select:focus { border-color: #888; box-shadow: 0 0 0 3px rgba(0,0,0,0.06); }
.select-arrow {
  position: absolute; right: 10px; top: 50%; transform: translateY(-50%) rotate(90deg);
  font-size: 16px; color: #999; pointer-events: none;
}
</style>
