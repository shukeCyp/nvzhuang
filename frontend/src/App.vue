<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="logo-mark">女</div>
        <span class="logo-text">女装助手</span>
      </div>
      <nav class="sidebar-nav">
        <a
          v-for="item in navItems"
          :key="item.path"
          :class="['nav-item', { active: $route.path === item.path || (item.path !== '/' && $route.path.startsWith(item.path)) }]"
          @click="$router.push(item.path)"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </a>
      </nav>
      <div class="sidebar-footer">v1.0.0</div>
    </aside>
    <main class="content">
      <router-view v-slot="{ Component }">
        <keep-alive>
          <component :is="Component" />
        </keep-alive>
      </router-view>
    </main>
  </div>
  <Toast ref="toastRef" />
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Toast from './components/Toast.vue'
import { setToastRef } from './composables/toast.js'

const toastRef = ref(null)
onMounted(() => setToastRef(toastRef))

const navItems = [
  { path: '/', label: '首页', icon: '⊞' },
  { path: '/crawler', label: '数据抓取', icon: '↓' },
  { path: '/debug', label: '调试', icon: '◫' },
  { path: '/settings', label: '设置', icon: '⚙' },
]
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Inter', sans-serif;
  background: #f4f4f5; color: #1a1a1a; height: 100vh; overflow: hidden;
}
.layout { display: flex; height: 100vh; }

.sidebar {
  width: 240px;
  background: #ffffff;
  border-right: 1px solid #e4e4e7;
  display: flex; flex-direction: column; flex-shrink: 0;
}

.sidebar-header {
  display: flex; align-items: center; gap: 10px;
  padding: 22px 20px 18px;
  border-bottom: 1px solid #e4e4e7;
}
.logo-mark {
  width: 30px; height: 30px; border-radius: 8px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700; color: #fff; flex-shrink: 0;
}
.logo-text { font-size: 14px; font-weight: 600; color: #18181b; letter-spacing: -0.3px; }

.sidebar-nav { padding: 12px 10px; display: flex; flex-direction: column; gap: 2px; flex: 1; }

.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 12px; border-radius: 8px; font-size: 13px;
  color: #71717a; cursor: pointer;
  transition: background 0.15s, color 0.15s; user-select: none;
}
.nav-item:hover { background: #f4f4f5; color: #18181b; }
.nav-item.active { background: #f4f4f5; color: #18181b; font-weight: 500; }
.nav-icon { font-size: 15px; width: 18px; text-align: center; }

.sidebar-footer {
  padding: 14px 20px; font-size: 11px; color: #a1a1aa;
  border-top: 1px solid #e4e4e7;
}

.content { flex: 1; overflow-y: auto; background: #f4f4f5; }
</style>
