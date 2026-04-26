<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">项目</h1>
        <p class="page-desc">扫描抓取结果目录，按项目展示类目、时间、国家和条数</p>
      </div>
      <button class="btn-refresh" :disabled="loading" @click="loadProjects">
        {{ loading ? '刷新中...' : '刷新' }}
      </button>
    </div>

    <div v-if="projects.length" class="project-grid">
      <article
        v-for="project in projects"
        :key="project.id"
        class="project-card"
        @click="openProject(project.id)"
      >
        <div class="card-top">
          <div class="project-category">{{ project.category_name }}</div>
          <div class="project-country">{{ project.region }}</div>
        </div>

        <div class="project-name">{{ project.name }}</div>

        <div class="meta-grid">
          <div class="meta-item">
            <span class="meta-label">时间</span>
            <span class="meta-value">{{ formatDate(project.crawl_date) }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">条数</span>
            <span class="meta-value">{{ project.total_count }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">图片数</span>
            <span class="meta-value">{{ project.image_count }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">业务日</span>
            <span class="meta-value">{{ formatBizDate(project.biz_date) }}</span>
          </div>
        </div>

        <div class="project-path">{{ project.path }}</div>
      </article>
    </div>

    <div v-else class="empty-card">
      <div class="empty-title">{{ loading ? '正在扫描项目...' : '暂无项目' }}</div>
      <p class="empty-desc">当前还没有检测到带 `summary.json` 的抓取项目目录。</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '../composables/toast.js'

const router = useRouter()
const toast = useToast()
const loading = ref(false)
const projects = ref([])

onMounted(() => {
  loadProjects()
})

async function loadProjects() {
  loading.value = true
  try {
    const api = await waitForApi()
    const result = await api.list_projects()
    if (result?.ok) {
      projects.value = result.projects || []
    } else {
      toast.error(result?.message || '项目加载失败')
    }
  } catch (error) {
    toast.error('项目加载失败：' + error)
  } finally {
    loading.value = false
  }
}

async function waitForApi(retries = 20, delay = 200) {
  for (let i = 0; i < retries; i += 1) {
    const api = window.pywebview?.api
    if (api?.list_projects) return api
    await sleep(delay)
  }
  throw new Error('pywebview API 未就绪')
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function formatDate(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString()
}

function formatBizDate(value) {
  if (!value || String(value).length !== 8) return value || '-'
  const text = String(value)
  return `${text.slice(0, 4)}-${text.slice(4, 6)}-${text.slice(6, 8)}`
}

function openProject(projectId) {
  router.push(`/workspace/${encodeURIComponent(projectId)}`)
}
</script>

<style scoped>
.page { padding: 32px; }
.page-header {
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}
.page-title { font-size: 22px; font-weight: 700; color: #18181b; letter-spacing: -0.6px; }
.page-desc { margin-top: 6px; font-size: 13px; color: #71717a; }
.btn-refresh {
  padding: 9px 18px;
  background: #18181b;
  color: #fff;
  border: none;
  border-radius: 999px;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
}
.btn-refresh:disabled { background: #d4d4d8; cursor: not-allowed; }
.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.project-card, .empty-card {
  background: linear-gradient(180deg, #ffffff 0%, #f7f7f8 100%);
  border: 1px solid #e4e4e7;
  border-radius: 18px;
  padding: 18px;
  box-shadow: 0 10px 24px rgba(24, 24, 27, 0.05);
}
.project-card {
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s, border-color 0.15s;
}
.project-card:hover {
  transform: translateY(-2px);
  border-color: #d4d4d8;
  box-shadow: 0 14px 28px rgba(24, 24, 27, 0.08);
}
.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}
.project-category {
  font-size: 14px;
  font-weight: 600;
  color: #18181b;
}
.project-country {
  padding: 4px 10px;
  border-radius: 999px;
  background: #18181b;
  color: #fff;
  font-size: 12px;
}
.project-name {
  font-size: 12px;
  color: #71717a;
  word-break: break-all;
  margin-bottom: 14px;
}
.meta-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 14px;
}
.meta-item {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #ececf0;
  border-radius: 12px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.meta-label {
  font-size: 11px;
  color: #71717a;
}
.meta-value {
  font-size: 13px;
  color: #18181b;
  font-weight: 600;
}
.project-path {
  font-size: 12px;
  color: #52525b;
  word-break: break-all;
  background: #f1f1f3;
  border-radius: 10px;
  padding: 10px;
}
.empty-title {
  font-size: 16px;
  font-weight: 600;
  color: #18181b;
  margin-bottom: 8px;
}
.empty-desc {
  font-size: 13px;
  color: #71717a;
}
</style>
