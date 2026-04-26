<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">设置</h1>
    </div>
    <div class="tab-bar">
      <button
        v-for="tab in tabs" :key="tab.key"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >{{ tab.label }}</button>
    </div>
    <div class="tab-content">

      <div v-if="activeTab === 'global'" class="card">
        <div class="field">
          <label>生图渠道</label>
          <AppSelect v-model="global.image_provider" :options="[{label:'云雾',value:'yunwu'},{label:'荷塘',value:'hotang'}]" />
        </div>
        <div class="field">
          <label>浏览器无头模式</label>
          <AppSelect v-model="global.headless" :options="[{label:'关闭（显示浏览器）',value:false},{label:'开启（后台运行）',value:true}]" />
        </div>
        <div class="field">
          <label>生图线程数</label>
          <input class="app-input" type="number" v-model.number="global.image_threads" min="1" max="10" />
        </div>
        <div class="field">
          <label>生视频线程数</label>
          <input class="app-input" type="number" v-model.number="global.video_threads" min="1" max="5" />
        </div>
        <button class="btn-primary" @click="saveGlobal">保存全局设置</button>
      </div>

      <div v-if="activeTab === 'llm'" class="card">
        <div class="field">
          <label>Base URL</label>
          <input class="app-input" v-model="llm.base_url" placeholder="例如 https://api.openai.com/v1" />
        </div>
        <div class="field">
          <label>API Key</label>
          <input class="app-input" v-model="llm.api_key" type="password" placeholder="输入 API Key" />
        </div>
        <div class="field">
          <label>Model</label>
          <input class="app-input" v-model="llm.model" placeholder="例如 gpt-4o" />
        </div>
        <button class="btn-primary" @click="saveLlm">保存 LLM 配置</button>
      </div>

      <div v-if="activeTab === 'crawl'" class="card">
        <div class="field">
          <label>Tabcut Cookie</label>
          <textarea v-model="crawl.cookie" placeholder="粘贴 tabcut.com 的 Cookie 字符串" rows="4"></textarea>
        </div>
        <div class="form-grid">
          <div class="field">
            <label>默认地区</label>
            <AppSelect v-model="crawl.region" :options="regions" />
          </div>
          <div class="field">
            <label>默认分类</label>
            <AppSelect v-model="crawl.categoryId" :options="categories" />
          </div>
          <div class="field">
            <label>默认抓取数量</label>
            <input class="app-input" type="number" v-model.number="crawl.count" min="1" max="200" />
          </div>
        </div>
        <button class="btn-primary" @click="save">保存</button>
      </div>

      <div v-if="activeTab === 'hotang'" class="card">
        <div class="field">
          <label>荷塘 Base URL</label>
          <input class="app-input" v-model="hotang.base_url" placeholder="例如 https://你的-flow2api 地址" />
        </div>
        <div class="field">
          <label>荷塘模型</label>
          <input class="app-input" v-model="hotang.model" placeholder="例如 gemini-2.5-flash-image-preview" />
        </div>
        <div class="field">
          <label>荷塘 API Key</label>
          <input class="app-input" v-model="hotang.api_key" type="password" placeholder="输入 flow2api API Key" />
        </div>
        <p class="hint">荷塘当前仅支持图生图，比例固定为 9:16。</p>
        <button class="btn-primary" @click="saveHotang">保存荷塘配置</button>
      </div>

      <div v-if="activeTab === 'yunwu'" class="card">
        <div class="field">
          <label>云雾 Base URL</label>
          <input class="app-input" v-model="yunwu.base_url" placeholder="例如 https://你的云雾地址" />
        </div>
        <div class="field">
          <label>云雾 API Key</label>
          <input class="app-input" v-model="yunwu.api_key" type="password" placeholder="输入云雾 API Key" />
        </div>
        <div class="field">
          <label>清晰度</label>
          <AppSelect v-model="yunwu.quality" :options="qualityOptions" />
        </div>
        <p class="hint">云雾固定使用 `gemini-3.1-flash-image-preview`，比例固定为 9:16。</p>
        <button class="btn-primary" @click="saveYunwu">保存云雾配置</button>
      </div>

      <div v-if="activeTab === 'kling'" class="card">
        <div class="field">
          <label>登录状态</label>
          <div class="kling-status">
            <span :class="['status-dot', kling.hasCookies ? 'ok' : 'none']"></span>
            <span>{{ kling.hasCookies ? 'Cookies 已保存' : '未登录' }}</span>
          </div>
        </div>
        <button class="btn-secondary" @click="klingLogin">打开浏览器登录</button>
        <div class="field">
          <label>模型</label>
          <AppSelect v-model="kling.model" :options="klingModels" />
        </div>
        <div class="field">
          <label>时长（秒）</label>
          <AppSelect v-model="kling.duration" :options="klingDurationOptions" />
        </div>
        <div class="field">
          <label>清晰度</label>
          <AppSelect v-model="kling.quality" :options="klingQualityOptions" />
        </div>
        <div class="field">
          <label>比例</label>
          <AppSelect v-model="kling.ratio" :options="klingRatioOptions" />
        </div>
        <button class="btn-primary" @click="saveKling">保存可灵配置</button>
      </div>

      <div v-if="activeTab === 'prompts'" class="card">
        <div class="field">
          <label>图片提示词</label>
          <textarea
            v-model="prompts.image_prompt"
            rows="6"
            placeholder="输入默认图片生成提示词模板"
          ></textarea>
        </div>
        <div class="field">
          <label>视频提示词</label>
          <textarea
            v-model="prompts.video_prompt"
            rows="6"
            placeholder="输入默认视频生成提示词模板"
          ></textarea>
        </div>
        <button class="btn-primary" @click="savePrompts">保存提示词配置</button>
      </div>

      <div v-if="activeTab === 'logs'" class="card">
        <div class="log-summary">
          <div class="stat-item">
            <span class="stat-label">日志文件数</span>
            <span class="stat-value">{{ logStats.files.length }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">总大小</span>
            <span class="stat-value">{{ formatSize(logStats.total_size) }}</span>
          </div>
        </div>
        <div class="log-files" v-if="logStats.files.length">
          <div v-for="f in logStats.files" :key="f.name" class="log-file-row">
            <span class="log-file-name">{{ f.name }}</span>
            <span class="log-file-size">{{ formatSize(f.size) }}</span>
          </div>
        </div>
        <p v-else class="hint">暂无日志文件</p>
        <div class="log-actions">
          <button class="btn-secondary" @click="packLogs">打包下载</button>
          <button class="btn-danger" @click="clearLogs">清理日志</button>
        </div>
      </div>

      <div v-if="activeTab === 'about'" class="card">
        <p class="hint">女装助手 v1.0.0</p>
        <p class="hint" style="margin-top:8px">数据保存目录：<code>data/</code></p>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useToast } from '../composables/toast.js'
import AppSelect from '../components/AppSelect.vue'

const toast = useToast()
const activeTab = ref('crawl')

const tabs = [
  { key: 'global', label: '全局设置' },
  { key: 'llm', label: 'LLM 配置' },
  { key: 'crawl', label: '抓取配置' },
  { key: 'hotang', label: '荷塘配置' },
  { key: 'yunwu', label: '云雾配置' },
  { key: 'kling', label: '可灵配置' },
  { key: 'prompts', label: '提示词配置' },
  { key: 'logs', label: '日志' },
  { key: 'about', label: '关于' },
]

const regions = ref([])
const categories = ref([])
const crawl = ref({ cookie: '', region: 'US', categoryId: '28', count: 48 })
const llm = ref({ base_url: '', api_key: '', model: '' })
const hotang = ref({ base_url: '', model: '', api_key: '' })
const yunwu = ref({ base_url: '', api_key: '', quality: '1K' })
const prompts = ref({ image_prompt: '', video_prompt: '' })
const kling = ref({ hasCookies: false, model: '2.6', duration: 5, quality: '720P', ratio: '16:9' })
const global = ref({ headless: false, image_threads: 2, video_threads: 1, image_provider: 'yunwu' })

const klingModels = [
  { label: '视频 2.6', value: '2.6' },
  { label: '视频 3.0', value: '3.0' },
]
const klingRatioOptions = [
  { label: '16:9', value: '16:9' },
  { label: '1:1', value: '1:1' },
  { label: '9:16', value: '9:16' },
]

const klingDurationOptions = computed(() =>
  kling.value.model === '3.0'
    ? Array.from({ length: 13 }, (_, i) => ({ label: `${i + 3}S`, value: i + 3 }))
    : [{ label: '5S', value: 5 }, { label: '10S', value: 10 }]
)
const klingQualityOptions = computed(() =>
  kling.value.model === '3.0'
    ? [{ label: '720P', value: '720P' }, { label: '1080P', value: '1080P' }, { label: '4K', value: '4K' }]
    : [{ label: '720P', value: '720P' }, { label: '1080P', value: '1080P' }]
)
const logStats = ref({ files: [], total_size: 0 })
const qualityOptions = [
  { label: '1K', value: '1K' },
  { label: '2K', value: '2K' },
  { label: '4K', value: '4K' },
]

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(2) + ' MB'
}

async function loadLogStats() {
  try { logStats.value = await window.pywebview.api.get_log_stats() } catch {}
}

async function packLogs() {
  try {
    const r = await window.pywebview.api.pack_logs()
    if (r.ok) toast.success('已打包：' + r.path)
    else toast.error(r.message)
  } catch { toast.error('打包失败') }
}

async function clearLogs() {
  try {
    const r = await window.pywebview.api.clear_logs()
    if (r.ok) { toast.success('日志已清理'); await loadLogStats() }
    else toast.error(r.message)
  } catch { toast.error('清理失败') }
}

onMounted(async () => {
  try {
    const meta = await window.pywebview.api.get_crawl_metadata()
    regions.value = meta?.regions || []
    categories.value = meta?.categories || []
    if (meta?.defaults) Object.assign(crawl.value, meta.defaults)
    const data = await window.pywebview.api.get_settings('crawl')
    if (data && Object.keys(data).length) Object.assign(crawl.value, data)
    const llmData = await window.pywebview.api.get_settings('llm')
    if (llmData && Object.keys(llmData).length) Object.assign(llm.value, llmData)
    const hotangData = await window.pywebview.api.get_settings('hotang')
    if (hotangData && Object.keys(hotangData).length) Object.assign(hotang.value, hotangData)
    const yunwuData = await window.pywebview.api.get_settings('yunwu')
    if (yunwuData && Object.keys(yunwuData).length) Object.assign(yunwu.value, yunwuData)
    const promptData = await window.pywebview.api.get_settings('prompts')
    if (promptData && Object.keys(promptData).length) Object.assign(prompts.value, promptData)
    const klingData = await window.pywebview.api.get_settings('kling')
    if (klingData && Object.keys(klingData).length) Object.assign(kling.value, klingData)
    const klingCookies = await window.pywebview.api.get_settings('kling_cookies')
    kling.value.hasCookies = !!(klingCookies?.cookies?.length)
    const globalData = await window.pywebview.api.get_settings('global')
    if (globalData && Object.keys(globalData).length) Object.assign(global.value, globalData)
  } catch {}
  loadLogStats()
})

async function save() {
  try {
    await window.pywebview.api.set_settings('crawl', crawl.value)
    toast.success('设置已保存')
  } catch {
    toast.error('保存失败')
  }
}

async function saveLlm() {
  try {
    await window.pywebview.api.set_settings('llm', llm.value)
    toast.success('LLM 配置已保存')
  } catch {
    toast.error('LLM 配置保存失败')
  }
}

async function saveHotang() {
  try {
    await window.pywebview.api.set_settings('hotang', hotang.value)
    toast.success('荷塘配置已保存')
  } catch {
    toast.error('荷塘配置保存失败')
  }
}

async function saveYunwu() {
  try {
    await window.pywebview.api.set_settings('yunwu', yunwu.value)
    toast.success('云雾配置已保存')
  } catch {
    toast.error('云雾配置保存失败')
  }
}

async function saveGlobal() {
  try {
    await window.pywebview.api.set_settings('global', global.value)
    toast.success('全局设置已保存')
  } catch { toast.error('全局设置保存失败') }
}

async function saveKling() {
  try {
    const { hasCookies, ...data } = kling.value
    await window.pywebview.api.set_settings('kling', data)
    toast.success('可灵配置已保存')
  } catch { toast.error('可灵配置保存失败') }
}

async function klingLogin() {
  try {
    const r = await window.pywebview.api.kling_login()
    if (r.ok) { kling.value.hasCookies = true; toast.success('登录成功，Cookies 已保存') }
    else toast.error(r.message || '登录失败')
  } catch { toast.error('登录失败') }
}

async function savePrompts() {
  try {
    await window.pywebview.api.set_settings('prompts', prompts.value)
    toast.success('提示词配置已保存')
  } catch {
    toast.error('提示词配置保存失败')
  }
}
</script>

<style scoped>
.page { padding: 32px; max-width: 680px; }
.page-header { margin-bottom: 20px; }
.page-title { font-size: 20px; font-weight: 700; color: #18181b; letter-spacing: -0.5px; }
.tab-bar { display: flex; margin-bottom: 20px; border-bottom: 1px solid #e4e4e7; flex-wrap: wrap; }
.tab-btn {
  padding: 8px 18px; font-size: 13px; background: none; border: none;
  border-bottom: 2px solid transparent; cursor: pointer; color: #71717a;
  margin-bottom: -1px; transition: color 0.15s;
}
.tab-btn.active { color: #18181b; border-bottom-color: #18181b; font-weight: 500; }
.tab-btn:hover:not(.active) { color: #18181b; }
.card {
  background: #fff; border: 1px solid #e4e4e7; border-radius: 12px; padding: 24px;
  display: flex; flex-direction: column; gap: 18px;
}
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.field { display: flex; flex-direction: column; gap: 7px; }
.field label { font-size: 12px; color: #52525b; font-weight: 500; }
textarea {
  width: 100%; padding: 10px; border: 1px solid #e4e4e7; border-radius: 8px;
  font-size: 12px; font-family: monospace; resize: vertical; outline: none;
}
textarea:focus { border-color: #888; box-shadow: 0 0 0 3px rgba(0,0,0,0.06); }
.app-input {
  padding: 8px 12px; border: 1px solid #e4e4e7; border-radius: 8px;
  font-size: 13px; outline: none; width: 100%;
}
.app-input:focus { border-color: #888; box-shadow: 0 0 0 3px rgba(0,0,0,0.06); }
.btn-primary {
  align-self: flex-start; padding: 9px 22px; background: #18181b; color: #fff;
  border: none; border-radius: 8px; font-size: 13px; font-weight: 500; cursor: pointer;
}
.btn-primary:hover { background: #3f3f46; }
.hint { font-size: 13px; color: #888; }
code { background: #f4f4f5; padding: 2px 6px; border-radius: 4px; font-size: 12px; }

.log-summary { display: flex; gap: 24px; }
.stat-item { display: flex; flex-direction: column; gap: 4px; }
.stat-label { font-size: 12px; color: #71717a; }
.stat-value { font-size: 20px; font-weight: 600; color: #18181b; }
.log-files { border: 1px solid #e4e4e7; border-radius: 8px; overflow: hidden; }
.log-file-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 12px; font-size: 13px; border-bottom: 1px solid #f4f4f5;
}
.log-file-row:last-child { border-bottom: none; }
.log-file-name { color: #3f3f46; font-family: monospace; }
.log-file-size { color: #a1a1aa; font-size: 12px; }
.log-actions { display: flex; gap: 8px; }
.btn-danger {
  padding: 9px 22px; background: #fff; color: #dc2626;
  border: 1px solid #fca5a5; border-radius: 8px; font-size: 13px; cursor: pointer;
}
.btn-danger:hover { background: #fef2f2; }
.btn-secondary {
  align-self: flex-start; padding: 9px 22px; background: #fff; color: #18181b;
  border: 1px solid #e4e4e7; border-radius: 8px; font-size: 13px; cursor: pointer;
}
.btn-secondary:hover { background: #f4f4f5; }
.kling-status { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #3f3f46; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; }
.status-dot.ok { background: #22c55e; }
.status-dot.none { background: #d4d4d8; }
</style>
