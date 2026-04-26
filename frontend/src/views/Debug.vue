<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">调试</h1>
      <p class="page-desc">调试接口、生成链路和输出结果</p>
    </div>

    <div class="tab-bar">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <div v-show="activeTab === 'yunwu' || activeTab === 'hotang'" class="card">
      <div class="field">
        <label>参考图</label>
        <input class="app-input" type="file" accept="image/*" @change="onFileChange" />
        <div v-if="sourceImageName" class="file-name">{{ sourceImageName }}</div>
      </div>

      <div v-if="sourceImageUrl" class="preview-wrap">
        <img :src="sourceImageUrl" class="source-img" />
      </div>

      <div class="field">
        <label>提示词</label>
        <textarea v-model="prompt" rows="6" placeholder="输入图生图提示词"></textarea>
      </div>

      <div v-if="activeTab === 'yunwu'" class="info-inline">
        云雾固定模型 `gemini-3.1-flash-image-preview`，当前清晰度：{{ yunwuQuality }}
      </div>
      <div v-if="activeTab === 'hotang'" class="info-inline">
        荷塘当前使用设置页里的模型，比例固定为 `9:16`，仅支持图生图
      </div>

      <button class="btn-primary" :disabled="running || !prompt.trim() || !imageB64" @click="generateImage">
        {{ running ? '生成中...' : '开始生成' }}
      </button>
    </div>

    <div v-show="activeTab === 'split'" class="card">
      <div class="field">
        <label>待切割图片</label>
        <input class="app-input" type="file" accept="image/*" @change="onFileChange" />
        <div v-if="sourceImageName" class="file-name">{{ sourceImageName }}</div>
      </div>

      <div v-if="sourceImageUrl" class="preview-wrap">
        <img :src="sourceImageUrl" class="source-img" />
      </div>

      <button class="btn-primary" :disabled="splitRunning || !imageB64" @click="splitImage">
        {{ splitRunning ? '切割中...' : '四宫格切割' }}
      </button>

      <div v-if="splitParts.length" class="split-grid">
        <div v-for="part in splitParts" :key="part.path" class="split-card">
          <img :src="`data:image/${part.ext};base64,${part.b64}`" class="split-img" />
          <div class="split-meta">第 {{ part.index }} 份 · {{ part.width }}×{{ part.height }}</div>
          <div class="split-path">{{ part.path }}</div>
        </div>
      </div>
    </div>

    <div v-show="activeTab === 'llm'" class="card">
      <div class="field">
        <label>商品图片</label>
        <input class="app-input" type="file" accept="image/*" @change="onSceneFileChange" />
        <div v-if="sceneImageName" class="file-name">{{ sceneImageName }}</div>
      </div>
      <div v-if="sceneImageUrl" class="preview-wrap">
        <img :src="sceneImageUrl" class="source-img" />
      </div>
      <div class="field">
        <label>商品名称</label>
        <input class="app-input" type="text" v-model="sceneTitle" placeholder="输入商品名称" />
      </div>
      <button class="btn-primary" :disabled="llmRunning || !sceneImageB64 || !sceneTitle.trim()" @click="sendLlm">
        {{ llmRunning ? '生成中...' : '生成场景名称' }}
      </button>
      <div v-if="llmResult" class="llm-result">{{ llmResult }}</div>
      <div v-if="llmError" class="llm-error">{{ llmError }}</div>
    </div>

    <div v-show="activeTab === 'kling'" class="card">
      <div class="field">
        <label>参考图片</label>
        <input class="app-input" type="file" accept="image/*" @change="onKlingFileChange" />
        <div v-if="klingImageName" class="file-name">{{ klingImageName }}</div>
      </div>
      <div v-if="klingImageUrl" class="preview-wrap">
        <img :src="klingImageUrl" class="source-img" />
      </div>
      <div class="field">
        <label>提示词</label>
        <textarea v-model="klingPrompt" rows="4" placeholder="输入视频提示词"></textarea>
      </div>
      <div class="info-inline">使用设置页可灵配置：模型 {{ klingSettings.model }} · {{ klingSettings.duration }}S · {{ klingSettings.quality }} · {{ klingSettings.ratio }}</div>
      <button class="btn-primary" :disabled="klingRunning || !klingPrompt.trim()" @click="generateKling">
        {{ klingRunning ? '生成中...' : '开始生成' }}
      </button>
      <div v-if="klingResult" class="llm-result">视频已保存：{{ klingResult }}</div>
      <div v-if="klingError" class="llm-error">{{ klingError }}</div>
    </div>

    <div v-show="activeTab === 'guide'" class="card">
      <div class="info-block">
        <div class="info-title">云雾图生图说明</div>
        <p>1. 先到“设置”页面填写云雾 `Base URL`、`API Key`、`清晰度`。</p>
        <p>2. 固定模型为 `gemini-3.1-flash-image-preview`。</p>
        <p>3. 比例固定为 `9:16`，清晰度从设置页读取 `1K / 2K / 4K`。</p>
      </div>
      <div class="info-block">
        <div class="info-title">荷塘图生图说明</div>
        <p>1. 先到“设置”页面填写荷塘 `Base URL`、`Model`、`API Key`。</p>
        <p>2. 荷塘只保留图生图，不再支持文生图。</p>
        <p>3. 生成成功后，后端返回本地文件路径，默认输出目录为 `data/generated_images/`。</p>
        <p>4. 荷塘走 `flow2api` 的 `POST /v1/chat/completions`。</p>
      </div>
      <div class="info-block">
        <div class="info-title">图片切割说明</div>
        <p>1. 上传一张图片后，会按四宫格方式等分切成四份。</p>
        <p>2. 切割结果会保存到 `data/debug_images/` 下的独立目录。</p>
      </div>
      <div class="info-block">
        <div class="info-title">当前接口</div>
        <code class="code-inline">
          云雾: POST /v1beta/models/:model:generateContent
          ｜ 荷塘: POST /v1/chat/completions
          ｜ 切割: split_image_four_grid
        </code>
      </div>
    </div>

    <div v-show="activeTab === 'history'" class="card">
      <div v-if="history.length" class="history-list">
        <div v-for="item in history" :key="item.id" class="history-item">
          <div class="history-time">{{ item.time }}</div>
          <div class="history-provider">{{ item.provider }}</div>
          <div class="history-path">{{ item.path }}</div>
        </div>
      </div>
      <p v-else class="hint">暂无生成记录</p>
    </div>

    <div v-if="resultB64" class="card">
      <div class="result-label">最近一次生成结果</div>
      <img :src="resultB64" class="result-img" />
      <div class="result-path">{{ resultPath }}</div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useToast } from '../composables/toast.js'

const toast = useToast()
const activeTab = ref('yunwu')
const prompt = ref('')
const running = ref(false)
const splitRunning = ref(false)
const resultPath = ref('')
const resultB64 = ref('')
const history = ref([])
const splitParts = ref([])
const imageB64 = ref('')
const imageMimeType = ref('')
const sourceImageUrl = ref('')
const sourceImageName = ref('')
const yunwuQuality = ref('1K')
const llmRunning = ref(false)
const llmResult = ref('')
const llmError = ref('')
const sceneImageB64 = ref('')
const sceneImageUrl = ref('')
const sceneImageName = ref('')
const sceneTitle = ref('')
const klingImageB64 = ref('')
const klingImageUrl = ref('')
const klingImageName = ref('')
const klingPrompt = ref('')
const klingRunning = ref(false)
const klingResult = ref('')
const klingError = ref('')
const klingSettings = ref({ model: '2.6', duration: 5, quality: '720P', ratio: '16:9' })

const tabs = [
  { key: 'yunwu', label: '云雾图生图' },
  { key: 'hotang', label: '荷塘图生图' },
  { key: 'split', label: '图片切割' },
  { key: 'llm', label: '场景生成' },
  { key: 'kling', label: '可灵视频' },
  { key: 'guide', label: '接口说明' },
  { key: 'history', label: '结果记录' },
]

onMounted(async () => {
  try {
    const settings = await window.pywebview.api.get_settings('yunwu')
    if (settings?.quality) yunwuQuality.value = settings.quality
    const ks = await window.pywebview.api.get_settings('kling')
    if (ks && Object.keys(ks).length) Object.assign(klingSettings.value, ks)
  } catch {}
})

function onFileChange(event) {
  const file = event.target.files?.[0]
  if (!file) {
    imageB64.value = ''
    imageMimeType.value = ''
    sourceImageUrl.value = ''
    sourceImageName.value = ''
    splitParts.value = []
    return
  }

  sourceImageName.value = file.name
  imageMimeType.value = file.type || 'image/png'

  const reader = new FileReader()
  reader.onload = () => {
    const result = String(reader.result || '')
    sourceImageUrl.value = result
    imageB64.value = result.includes(',') ? result.split(',')[1] : result
    splitParts.value = []
  }
  reader.readAsDataURL(file)
}

async function generateImage() {
  running.value = true
  resultPath.value = ''
  try {
    const apiName = activeTab.value === 'yunwu' ? 'generate_yunwu_image' : 'generate_hotang_image'
    const providerLabel = activeTab.value === 'yunwu' ? '云雾' : '荷塘'
    const result = await window.pywebview.api[apiName]({
      prompt: prompt.value,
      image_b64: imageB64.value,
      mime_type: imageMimeType.value,
    })
    if (result.ok) {
      resultPath.value = result.path
      resultB64.value = `data:image/${result.ext};base64,${result.b64}`
      history.value.unshift({
        id: `${Date.now()}-${result.path}`,
        time: new Date().toLocaleString(),
        provider: providerLabel,
        path: result.path,
      })
      const a = document.createElement('a')
      a.href = resultB64.value
      a.download = result.path.split('/').pop() || `${activeTab.value}.${result.ext}`
      a.click()
      toast.success('图片生成完成')
    } else {
      toast.error(result.message || '图片生成失败')
    }
  } catch (error) {
    toast.error('图片生成失败：' + error)
  } finally {
    running.value = false
  }
}

function onKlingFileChange(event) {
  const file = event.target.files?.[0]
  if (!file) { klingImageB64.value = ''; klingImageUrl.value = ''; klingImageName.value = ''; return }
  klingImageName.value = file.name
  const reader = new FileReader()
  reader.onload = () => {
    const result = String(reader.result || '')
    klingImageUrl.value = result
    klingImageB64.value = result.includes(',') ? result.split(',')[1] : result
  }
  reader.readAsDataURL(file)
}

async function generateKling() {
  klingRunning.value = true
  klingResult.value = ''
  klingError.value = ''
  try {
    const res = await window.pywebview.api.generate_kling_video({
      image_b64: klingImageB64.value,
      prompt: klingPrompt.value,
    })
    if (res.ok) klingResult.value = res.path
    else klingError.value = res.message || '生成失败'
  } catch (e) {
    klingError.value = '生成失败：' + e
  } finally {
    klingRunning.value = false
  }
}

function onSceneFileChange(event) {
  const file = event.target.files?.[0]
  if (!file) { sceneImageB64.value = ''; sceneImageUrl.value = ''; sceneImageName.value = ''; return }
  sceneImageName.value = file.name
  const reader = new FileReader()
  reader.onload = () => {
    const result = String(reader.result || '')
    sceneImageUrl.value = result
    sceneImageB64.value = result.includes(',') ? result.split(',')[1] : result
  }
  reader.readAsDataURL(file)
}

async function sendLlm() {
  llmRunning.value = true
  llmResult.value = ''
  llmError.value = ''
  try {
    const res = await window.pywebview.api.debug_scene_prompt({
      image_b64: sceneImageB64.value,
      title: sceneTitle.value,
    })
    if (res.ok) llmResult.value = res.scene
    else llmError.value = res.message || '场景生成失败'
  } catch (e) {
    llmError.value = '场景生成失败：' + e
  } finally {
    llmRunning.value = false
  }
}

async function splitImage() {
  splitRunning.value = true
  splitParts.value = []
  try {
    const result = await window.pywebview.api.split_image_four_grid({
      image_b64: imageB64.value,
      mime_type: imageMimeType.value,
    })
    if (result.ok) {
      splitParts.value = result.parts || []
      toast.success('图片切割完成')
    } else {
      toast.error(result.message || '图片切割失败')
    }
  } catch (error) {
    toast.error('图片切割失败：' + error)
  } finally {
    splitRunning.value = false
  }
}
</script>

<style scoped>
.page { padding: 32px; max-width: 980px; }
.page-header { margin-bottom: 24px; }
.page-title { font-size: 20px; font-weight: 700; color: #18181b; letter-spacing: -0.5px; }
.page-desc { font-size: 13px; color: #888; margin-top: 4px; }
.tab-bar { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.tab-btn {
  padding: 8px 14px; border-radius: 999px; border: 1px solid #e4e4e7;
  background: #fff; color: #71717a; font-size: 13px; cursor: pointer;
}
.tab-btn.active {
  background: #18181b; color: #fff; border-color: #18181b;
}
.card {
  background: #fff; border: 1px solid #e4e4e7; border-radius: 12px;
  padding: 24px; margin-bottom: 16px;
}
.field { display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px; }
.field label { font-size: 12px; color: #52525b; font-weight: 500; }
textarea {
  width: 100%; padding: 10px; border: 1px solid #e4e4e7; border-radius: 8px;
  font-size: 13px; resize: vertical; outline: none;
}
.app-input {
  padding: 8px 12px; border: 1px solid #e4e4e7; border-radius: 8px;
  font-size: 13px; outline: none; width: 100%;
}
.btn-primary {
  padding: 9px 22px; background: #18181b; color: #fff;
  border: none; border-radius: 8px; font-size: 13px; font-weight: 500; cursor: pointer;
}
.btn-primary:disabled { background: #d4d4d8; cursor: not-allowed; }
.result-label, .info-title { font-size: 12px; color: #71717a; margin-bottom: 8px; }
.result-img { max-width: 100%; border-radius: 8px; margin-bottom: 8px; }
.result-path, .history-path, .code-inline, .split-path {
  font-size: 13px; color: #18181b; word-break: break-all;
}
.result-path, .history-item, .info-block, .split-card {
  background: #f4f4f5; border-radius: 8px; padding: 12px;
}
.history-list { display: flex; flex-direction: column; gap: 10px; }
.history-time, .history-provider, .file-name, .info-inline, .split-meta { font-size: 12px; color: #71717a; }
.history-time, .history-provider { margin-bottom: 6px; }
.info-block { margin-bottom: 12px; }
.hint { font-size: 13px; color: #888; }
.code-inline {
  display: inline-block; background: #fff; border: 1px solid #e4e4e7;
  border-radius: 6px; padding: 6px 8px;
  white-space: pre-wrap;
}
.preview-wrap {
  margin-bottom: 16px; padding: 12px; border-radius: 8px; background: #f4f4f5;
}
.source-img {
  display: block; max-width: 240px; max-height: 360px; border-radius: 8px;
}
.split-grid {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.split-img {
  width: 100%;
  border-radius: 8px;
  display: block;
  margin-bottom: 8px;
}
.llm-result {
  margin-top: 12px; padding: 12px; background: #f4f4f5;
  border-radius: 8px; font-size: 13px; white-space: pre-wrap; word-break: break-all;
}
.llm-error {
  margin-top: 12px; padding: 12px; background: #fef2f2;
  border-radius: 8px; font-size: 13px; color: #dc2626; word-break: break-all;
}
</style>
