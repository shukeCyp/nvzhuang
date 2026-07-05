<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">数据抓取</h1>
      <p class="page-desc">从 Tabcut 抓取 TikTok Shop 商品排名数据</p>
    </div>

    <div class="card">
      <div class="form-grid">
        <div class="form-item">
          <label>Cookie 状态</label>
          <div class="cookie-row">
            <span :class="['badge', cookieSet ? 'badge-green' : 'badge-orange']">
              {{ cookieSet ? '已配置' : '未配置' }}
            </span>
            <button class="btn-link" @click="showCookieModal = true">管理</button>
          </div>
        </div>
        <div class="form-item">
          <label>地区</label>
          <AppSelect v-model="form.region" :options="regions" />
        </div>
        <div class="form-item">
          <label>商品分类</label>
          <AppSelect v-model="form.categoryId" :options="categories" />
        </div>
        <div class="form-item">
          <label>抓取数量</label>
          <input class="app-input" type="number" v-model.number="form.count" min="1" max="200" />
        </div>
        <div class="form-item form-item-wide">
          <label>榜单类型</label>
          <div class="choice-group">
            <label v-for="item in rankTypes" :key="item.value" class="choice-item">
              <input type="radio" :value="item.value" v-model.number="form.rankType" />
              <span>{{ item.label }}</span>
            </label>
          </div>
        </div>
        <div class="form-item form-item-wide">
          <label>{{ dateFieldLabel }}</label>
          <input
            v-if="form.rankType === 1"
            class="app-input"
            type="date"
            v-model="form.bizDate"
          />
          <input
            v-else-if="form.rankType === 2"
            class="app-input"
            type="week"
            v-model="form.bizWeek"
          />
          <input
            v-else
            class="app-input"
            type="month"
            v-model="form.bizMonth"
          />
        </div>
        <div class="form-item form-item-wide">
          <label>店铺类型</label>
          <div class="checkbox-group">
            <label v-for="item in sellerTypes" :key="item.value" class="checkbox-item">
              <input type="checkbox" :value="item.value" v-model="form.sellerTypes" />
              <span>{{ item.label }}</span>
            </label>
          </div>
        </div>
      </div>
      <button class="btn-primary" :disabled="running || !cookieSet" @click="startCrawl">
        {{ running ? '抓取中...' : '开始抓取' }}
      </button>
    </div>

    <div class="card" v-if="running || logs.length">
      <div class="progress-bar-bg">
        <div class="progress-bar-fill" :style="{ width: progress + '%' }"></div>
      </div>
      <div class="progress-text">{{ statusMessage || '准备中...' }} {{ progress }}%</div>
      <div class="log-box" ref="logBox">
        <div v-for="(line, i) in logs" :key="i" class="log-line">{{ line }}</div>
      </div>
    </div>

    <!-- Cookie 弹窗 -->
    <div class="modal-mask" v-if="showCookieModal" @click.self="showCookieModal = false">
      <div class="modal">
        <h2>配置 Tabcut Cookie</h2>
        <textarea v-model="cookieInput" placeholder="粘贴 tabcut.com 的 Cookie 字符串" rows="5"></textarea>
        <div class="modal-actions">
          <button class="btn-secondary" @click="showCookieModal = false">取消</button>
          <button class="btn-primary" @click="saveCookie">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useToast } from '../composables/toast.js'
import AppSelect from '../components/AppSelect.vue'

const toast = useToast()

const regions = ref([])
const categories = ref([])
const sellerTypes = ref([])
const rankTypes = ref([
  { label: '日榜', value: 1 },
  { label: '周榜', value: 2 },
  { label: '月榜', value: 3 },
])
const form = ref({
  region: 'US',
  categoryId: '28',
  count: 48,
  sellerTypes: ['full_managed'],
  rankType: 1,
  bizDate: defaultDay(),
  bizWeek: defaultWeek(),
  bizMonth: defaultMonth(),
})
const running = ref(false)
const progress = ref(0)
const statusMessage = ref('')
const logs = ref([])
const logBox = ref(null)
const cookieSet = ref(false)
const showCookieModal = ref(false)
const cookieInput = ref('')
let crawlPollTimer = null
let currentTaskId = ''
let lastLogId = 0

const dateFieldLabel = computed(() => {
  if (form.value.rankType === 2) return '选择周'
  if (form.value.rankType === 3) return '选择月'
  return '选择日期'
})

onMounted(async () => {
  try {
    const meta = await window.pywebview.api.get_crawl_metadata()
    regions.value = meta?.regions || []
    categories.value = meta?.categories || []
    rankTypes.value = meta?.rank_types || rankTypes.value
    sellerTypes.value = meta?.seller_types || [
      { label: '跨境店', value: 'over_sea' },
      { label: '本土店', value: 'local' },
      { label: '全托管店', value: 'full_managed' },
    ]
    if (meta?.defaults) {
      Object.assign(form.value, meta.defaults)
    }
    const data = await window.pywebview.api.get_settings('crawl')
    if (data && Object.keys(data).length) {
      if (data.cookie) { cookieSet.value = true; cookieInput.value = data.cookie }
      if (data.region) form.value.region = data.region
      if (data.categoryId) form.value.categoryId = data.categoryId
      if (data.count) form.value.count = data.count
      if (data.rankType) form.value.rankType = Number(data.rankType) || 1
      if (data.bizDate) form.value.bizDate = data.bizDate
      if (data.bizWeek) form.value.bizWeek = data.bizWeek
      if (data.bizMonth) form.value.bizMonth = data.bizMonth
      if (Array.isArray(data.sellerTypes)) form.value.sellerTypes = data.sellerTypes
      else if (data.seller_type) form.value.sellerTypes = String(data.seller_type).split(',').filter(Boolean)
    }
    if (!cookieInput.value) {
      const saved = localStorage.getItem('tabcut_cookie')
      if (saved) { cookieSet.value = true; cookieInput.value = saved }
    }
  } catch {
    const saved = localStorage.getItem('tabcut_cookie')
    if (saved) { cookieSet.value = true; cookieInput.value = saved }
  }
})

onBeforeUnmount(() => {
  stopPolling()
})

async function persistCrawlSettings() {
  await window.pywebview.api.set_settings('crawl', {
    ...form.value,
    sellerTypes: normalizeSellerTypes(form.value.sellerTypes),
    cookie: cookieInput.value.trim(),
  })
}

async function saveCookie() {
  try {
    await persistCrawlSettings()
    cookieSet.value = !!cookieInput.value.trim()
    localStorage.setItem('tabcut_cookie', cookieInput.value.trim())
    showCookieModal.value = false
    toast.success('Cookie 已保存')
  } catch {
    toast.error('Cookie 保存失败')
  }
}

async function startCrawl() {
  running.value = true
  progress.value = 0
  statusMessage.value = '正在创建抓取任务'
  logs.value = []
  stopPolling()
  lastLogId = 0
  const cookie = cookieInput.value.trim()
  const selectedCategory = categories.value.find((item) => item.value === form.value.categoryId)
  const selectedSellerTypes = normalizeSellerTypes(form.value.sellerTypes)
  const bizDate = selectedBizDate()
  try {
    await persistCrawlSettings()
    const result = await window.pywebview.api.start_crawl({
      cookie, region: form.value.region,
      category_id: form.value.categoryId,
      category_name: selectedCategory?.label || form.value.categoryId,
      seller_type: selectedSellerTypes.join(','),
      rank_type: form.value.rankType,
      biz_date: bizDate,
      count: form.value.count,
    })
    if (!result.ok || !result.task_id) {
      throw new Error(result.message || '创建抓取任务失败')
    }
    currentTaskId = result.task_id
    lastLogId = result.start_log_id || 0
    addLog('抓取任务已启动')
    startPolling()
  } catch (e) {
    addLog('错误：' + e)
    toast.error('抓取失败：' + e)
    running.value = false
    statusMessage.value = '抓取启动失败'
  }
}

function addLog(line) {
  logs.value.push(line)
  nextTick(() => { if (logBox.value) logBox.value.scrollTop = logBox.value.scrollHeight })
}

function stopPolling() {
  if (crawlPollTimer) {
    clearInterval(crawlPollTimer)
    crawlPollTimer = null
  }
}

function startPolling() {
  crawlPollTimer = setInterval(pollStatus, 800)
  pollStatus()
}

async function pollStatus() {
  if (!currentTaskId) return
  try {
    const result = await window.pywebview.api.get_crawl_status(currentTaskId, lastLogId)
    if (!result.ok) {
      stopPolling()
      running.value = false
      addLog(result.message || '获取抓取状态失败')
      toast.error(result.message || '获取抓取状态失败')
      return
    }

    progress.value = result.progress || 0
    statusMessage.value = result.message || statusMessage.value
    if (Array.isArray(result.logs)) {
      for (const item of result.logs) {
        addLog(item.line)
      }
    }
    lastLogId = result.last_log_id || lastLogId

    if (result.status === 'completed') {
      stopPolling()
      running.value = false
      progress.value = 100
      statusMessage.value = result.message || '抓取完成'
      if (result.message) addLog(result.message)
      toast.success(result.message || '抓取完成')
      return
    }

    if (result.status === 'failed') {
      stopPolling()
      running.value = false
      statusMessage.value = result.message || '抓取失败'
      if (result.message) addLog(result.message)
      toast.error(result.message || '抓取失败')
    }
  } catch (error) {
    stopPolling()
    running.value = false
    statusMessage.value = '获取抓取状态失败'
    addLog('轮询状态失败：' + error)
    toast.error('获取抓取进度失败：' + error)
  }
}

function normalizeSellerTypes(values) {
  const selected = Array.isArray(values) ? values.filter(Boolean) : []
  return selected.length ? selected : ['full_managed']
}

function pad2(value) {
  return String(value).padStart(2, '0')
}

function formatDate(date) {
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`
}

function formatBizDate(date) {
  return formatDate(date).replaceAll('-', '')
}

function defaultDay() {
  const date = new Date()
  date.setDate(date.getDate() - 1)
  return formatDate(date)
}

function defaultWeek() {
  const today = new Date()
  const day = today.getDay() || 7
  const currentMonday = new Date(today)
  currentMonday.setDate(today.getDate() - day + 1)
  const previousMonday = new Date(currentMonday)
  previousMonday.setDate(currentMonday.getDate() - 7)
  return weekValue(previousMonday)
}

function defaultMonth() {
  const date = new Date()
  date.setMonth(date.getMonth() - 1, 1)
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}`
}

function weekValue(date) {
  const target = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()))
  const day = target.getUTCDay() || 7
  target.setUTCDate(target.getUTCDate() + 4 - day)
  const yearStart = new Date(Date.UTC(target.getUTCFullYear(), 0, 1))
  const week = Math.ceil((((target - yearStart) / 86400000) + 1) / 7)
  return `${target.getUTCFullYear()}-W${pad2(week)}`
}

function endDateOfWeek(week) {
  const match = String(week || '').match(/^(\d{4})-W(\d{2})$/)
  if (!match) return null
  const year = Number(match[1])
  const weekNo = Number(match[2])
  const jan4 = new Date(Date.UTC(year, 0, 4))
  const jan4Day = jan4.getUTCDay() || 7
  const monday = new Date(jan4)
  monday.setUTCDate(jan4.getUTCDate() - jan4Day + 1 + (weekNo - 1) * 7)
  const sunday = new Date(monday)
  sunday.setUTCDate(monday.getUTCDate() + 6)
  return new Date(sunday.getUTCFullYear(), sunday.getUTCMonth(), sunday.getUTCDate())
}

function endDateOfMonth(month) {
  const match = String(month || '').match(/^(\d{4})-(\d{2})$/)
  if (!match) return null
  return new Date(Number(match[1]), Number(match[2]), 0)
}

function selectedBizDate() {
  if (form.value.rankType === 2) {
    return formatBizDate(endDateOfWeek(form.value.bizWeek) || endDateOfWeek(defaultWeek()))
  }
  if (form.value.rankType === 3) {
    return formatBizDate(endDateOfMonth(form.value.bizMonth) || endDateOfMonth(defaultMonth()))
  }
  return String(form.value.bizDate || defaultDay()).replaceAll('-', '')
}
</script>

<style scoped>
.page { padding: 32px; max-width: 720px; }
.page-header { margin-bottom: 24px; }
.page-title { font-size: 20px; font-weight: 700; color: #18181b; letter-spacing: -0.5px; }
.page-desc { font-size: 13px; color: #888; margin-top: 4px; }

.card {
  background: #fff; border: 1px solid #e4e4e7; border-radius: 12px;
  padding: 24px; margin-bottom: 16px;
}

.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-bottom: 20px; }
.form-item-wide { grid-column: 1 / -1; }
.form-item { display: flex; flex-direction: column; gap: 7px; }
.form-item label { font-size: 12px; color: #52525b; font-weight: 500; }

.checkbox-group, .choice-group { display: flex; flex-wrap: wrap; gap: 10px; min-height: 36px; align-items: center; }
.checkbox-item, .choice-item {
  display: inline-flex; align-items: center; gap: 6px; padding: 7px 10px;
  border: 1px solid #e4e4e7; border-radius: 8px; font-size: 13px; color: #27272a;
  cursor: pointer; user-select: none; background: #fff;
}
.checkbox-item input, .choice-item input { margin: 0; }

.app-input {
  padding: 8px 12px; border: 1px solid #e0e0e0; border-radius: 8px;
  font-size: 13px; color: #1a1a1a; outline: none; width: 100%;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.app-input:hover { border-color: #c0c0c0; }
.app-input:focus { border-color: #888; box-shadow: 0 0 0 3px rgba(0,0,0,0.06); }

.cookie-row { display: flex; align-items: center; gap: 8px; height: 36px; }
.badge { font-size: 12px; padding: 3px 10px; border-radius: 20px; font-weight: 500; }
.badge-green { background: #dcfce7; color: #166534; }
.badge-orange { background: #fff7ed; color: #9a3412; }
.btn-link { font-size: 12px; color: #6366f1; background: none; border: none; cursor: pointer; }
.btn-link:hover { text-decoration: underline; }

.btn-primary {
  padding: 9px 22px; background: #18181b; color: #fff;
  border: none; border-radius: 8px; font-size: 13px; font-weight: 500; cursor: pointer;
  transition: background 0.15s;
}
.btn-primary:hover:not(:disabled) { background: #3f3f46; }
.btn-primary:disabled { background: #d4d4d8; cursor: not-allowed; }
.btn-secondary {
  padding: 9px 22px; background: #fff; color: #18181b;
  border: 1px solid #e4e4e7; border-radius: 8px; font-size: 13px; cursor: pointer;
}

.progress-bar-bg { height: 4px; background: #f4f4f5; border-radius: 2px; margin-bottom: 14px; }
.progress-bar-fill { height: 100%; background: #6366f1; border-radius: 2px; transition: width 0.3s; }
.progress-text { font-size: 12px; color: #52525b; margin-bottom: 10px; }
.log-box {
  background: #fafafa; border: 1px solid #f0f0f0; border-radius: 8px;
  padding: 12px 14px; height: 200px; overflow-y: auto;
  font-size: 12px; font-family: 'SF Mono', monospace;
}
.log-line { color: #52525b; line-height: 1.7; }

.modal-mask {
  position: fixed; inset: 0; background: rgba(0,0,0,0.25);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.modal {
  background: #fff; border-radius: 12px; padding: 28px; width: 500px;
  display: flex; flex-direction: column; gap: 16px;
  box-shadow: 0 8px 40px rgba(0,0,0,0.12);
}
.modal h2 { font-size: 15px; font-weight: 600; }
.modal textarea {
  width: 100%; padding: 10px; border: 1px solid #e4e4e7; border-radius: 8px;
  font-size: 12px; font-family: monospace; resize: vertical; outline: none;
}
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; }
</style>
