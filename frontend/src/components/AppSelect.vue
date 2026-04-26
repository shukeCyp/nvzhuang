<template>
  <div class="select-wrap">
    <select :value="modelValue" @change="$emit('update:modelValue', $event.target.value)">
      <option v-for="opt in options" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
    </select>
    <span class="select-arrow">›</span>
  </div>
</template>

<script setup>
defineProps({ modelValue: String, options: Array })
defineEmits(['update:modelValue'])
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
