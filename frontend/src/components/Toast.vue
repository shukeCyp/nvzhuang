<template>
  <teleport to="body">
    <div class="toast-container">
      <transition-group name="toast">
        <div v-for="t in toasts" :key="t.id" :class="['toast', t.type]">
          <span class="toast-icon">{{ icons[t.type] }}</span>
          <span>{{ t.message }}</span>
        </div>
      </transition-group>
    </div>
  </teleport>
</template>

<script setup>
import { ref } from 'vue'

const toasts = ref([])
const icons = { success: '✓', warning: '!', error: '✕' }
let seq = 0

function show(message, type = 'success', duration = 3000) {
  const id = ++seq
  toasts.value.push({ id, message, type })
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }, duration)
}

defineExpose({ show })
</script>

<style scoped>
.toast-container {
  position: fixed; top: 20px; right: 20px;
  display: flex; flex-direction: column; gap: 8px; z-index: 9999;
}
.toast {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 16px; border-radius: 8px; font-size: 13px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.12); min-width: 220px;
}
.toast.success { background: #f0faf2; color: #1e6e30; border: 1px solid #b7e4c7; }
.toast.warning { background: #fff8ed; color: #92400e; border: 1px solid #fcd38d; }
.toast.error   { background: #fff1f1; color: #991b1b; border: 1px solid #fca5a5; }
.toast-icon { font-weight: 700; }
.toast-enter-active, .toast-leave-active { transition: all 0.25s ease; }
.toast-enter-from { opacity: 0; transform: translateX(20px); }
.toast-leave-to   { opacity: 0; transform: translateX(20px); }
</style>
