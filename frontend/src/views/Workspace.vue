<template>
  <div class="page">
    <div class="page-header">
      <div>
        <button class="back-link" @click="$router.push('/')">返回项目</button>
        <h1 class="page-title">工作台</h1>
        <p class="page-desc">
          {{ project.category_name || '-' }} · {{ project.region || '-' }} · {{ formatDate(project.crawl_date) }} · {{ items.length }} 条
        </p>
      </div>

      <div class="toolbar">
        <button class="toolbar-btn" @click="openMainBatchDialog">批量主图</button>
        <button class="toolbar-btn" @click="openRoleDialog">批量角色图</button>
        <button class="toolbar-btn primary" @click="openBatchDialog('image')">图片生成</button>
        <button class="toolbar-btn" @click="openBatchDialog('video')">视频生成</button>
        <button class="btn-refresh" :disabled="loading" @click="loadWorkspace">
          {{ loading ? '刷新中...' : '刷新' }}
        </button>
      </div>
    </div>

    <div v-if="items.length" class="table-wrap">
      <table class="workspace-table">
        <thead>
          <tr>
            <th>主图</th>
            <th>角色图</th>
            <th>视频</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.product_id">
            <td class="main-col">
              <img
                v-if="item.main_image_url"
                :src="item.main_image_url"
                class="ratio-media main-media clickable"
                @click="openMainImageDialog(item)"
              />
              <div v-else class="ratio-media main-media placeholder-card clickable" @click="openMainImageDialog(item)">暂无主图</div>
            </td>

            <td class="roles-col">
              <div class="roles-grid">
                <template v-for="index in 4" :key="`${item.product_id}-${index}`">
                  <div class="role-img-wrap" :class="{ selected: item.selected_role_index === index - 1 }"
                    @click="selectRoleImage(item, index - 1)"
                    @contextmenu.prevent="openPreview(item.role_images[index - 1])">
                    <img
                      v-if="item.role_images?.[index - 1]"
                      :src="item.role_images[index - 1]"
                      class="ratio-media"
                    />
                    <div v-else class="ratio-media placeholder-card">角色图 {{ index }}</div>
                    <span v-if="item.selected_role_index === index - 1" class="role-selected-badge">已选</span>
                  </div>
                </template>
              </div>
            </td>

            <td class="video-col">
              <div v-if="item.video_url" class="video-thumb clickable" @click="openPreview(item.video_url, 'video')">
                <video
                  :key="item.video_url"
                  :src="item.video_url"
                  class="ratio-media video-media"
                  preload="auto"
                  muted
                  autoplay
                  loop
                  playsinline
                />
                <div class="play-icon">▶</div>
              </div>
              <div v-else class="ratio-media video-media placeholder-card">视频待生成</div>
            </td>

            <td class="action-col">
              <div class="action-stack">
                <button class="action-btn primary"
                  :disabled="isItemBusy(item)"
                  @click="handleGenerateImage(item)">
                  {{ imageButtonLabel(item) }}
                </button>
                <button class="action-btn"
                  :disabled="isItemBusy(item)"
                  @click="handleGenerateVideo(item)">
                  {{ videoButtonLabel(item) }}
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else class="empty-card">
      <div class="empty-title">{{ loading ? '正在加载商品...' : '暂无商品数据' }}</div>
      <p class="empty-desc">当前项目下没有读取到 `items/*.json`。</p>
    </div>

    <div v-if="preview.visible" class="modal-mask" @click.self="preview.visible = false">
      <div class="preview-modal">
        <button class="modal-close preview-close" @click="preview.visible = false">关闭</button>
        <video v-if="preview.type === 'video'" :src="preview.url" controls autoplay class="preview-media" />
        <img v-else :src="preview.url" class="preview-media" />
      </div>
    </div>

    <div v-if="dialogItem" class="modal-mask" @click.self="closeMainImageDialog">
      <div class="modal-card">
        <div class="modal-header">
          <div>
            <div class="modal-title">选择主图</div>
            <div class="modal-desc">{{ dialogItem.title }}</div>
          </div>
          <button class="modal-close" @click="closeMainImageDialog">关闭</button>
        </div>

        <div v-if="dialogItem.product_images?.length" class="picker-grid">
          <button
            v-for="(image, index) in dialogItem.product_images"
            :key="`${dialogItem.product_id}-${index}`"
            :class="['picker-card', { active: dialogItem.main_image_index === index }]"
            @click="selectMainImage(dialogItem.product_id, index)"
          >
            <img :src="toFileUrl(image)" class="picker-image" />
            <span class="picker-index">第 {{ index + 1 }} 张</span>
          </button>
        </div>
        <div v-else class="empty-picker">这个商品没有可选图片。</div>
      </div>
    </div>

    <div v-if="batchDialog.visible" class="modal-mask" @click.self="closeBatchDialog">
      <div class="modal-card batch-modal">
        <div class="modal-header">
          <div>
            <div class="modal-title">{{ batchDialog.type === 'image' ? '批量图片生成' : '批量视频生成' }}</div>
            <div class="modal-desc">选择执行模式后再开始批量任务。</div>
          </div>
          <button class="modal-close" @click="closeBatchDialog">关闭</button>
        </div>

        <div class="batch-stats">
          <div class="stat-box">
            <span class="stat-label">总共</span>
            <span class="stat-value">{{ batchDialog.total }}</span>
          </div>
          <div class="stat-box">
            <span class="stat-label">缺少</span>
            <span class="stat-value">{{ batchDialog.missing }}</span>
          </div>
        </div>

        <div class="mode-group">
          <label class="mode-card">
            <input v-model="batchDialog.mode" type="radio" value="missing" />
            <div>
              <div class="mode-title">补全模式</div>
              <div class="mode-desc">只处理当前缺少结果的条目。</div>
            </div>
          </label>
          <label class="mode-card">
            <input v-model="batchDialog.mode" type="radio" value="all" />
            <div>
              <div class="mode-title">全量模式</div>
              <div class="mode-desc">重新处理全部条目。</div>
            </div>
          </label>
        </div>

        <div class="batch-actions">
          <button class="action-btn" @click="closeBatchDialog">取消</button>
          <button class="action-btn primary" @click="confirmBatchAction">开始</button>
        </div>
      </div>
    </div>
    <div v-if="mainBatchDialog.visible" class="modal-mask" @click.self="mainBatchDialog.visible = false">
      <div class="modal-card batch-modal">
        <div class="modal-header">
          <div>
            <div class="modal-title">批量选择主图</div>
            <div class="modal-desc">选择第几张主图应用到所有商品。</div>
          </div>
          <button class="modal-close" @click="mainBatchDialog.visible = false">关闭</button>
        </div>
        <div class="mode-group">
          <label v-for="n in 9" :key="n" class="mode-card">
            <input v-model="mainBatchDialog.index" type="radio" :value="n" />
            <div><div class="mode-title">第 {{ n }} 张</div></div>
          </label>
        </div>
        <div class="batch-actions">
          <button class="action-btn" @click="mainBatchDialog.visible = false">取消</button>
          <button class="action-btn primary" @click="confirmMainBatch">应用</button>
        </div>
      </div>
    </div>
    <div v-if="roleDialog.visible" class="modal-mask" @click.self="roleDialog.visible = false">
      <div class="modal-card batch-modal">
        <div class="modal-header">
          <div>
            <div class="modal-title">批量选择角色图</div>
            <div class="modal-desc">选择第几个角色图应用到所有商品。</div>
          </div>
          <button class="modal-close" @click="roleDialog.visible = false">关闭</button>
        </div>
        <div class="mode-group">
          <label v-for="n in 4" :key="n" class="mode-card">
            <input v-model="roleDialog.index" type="radio" :value="n - 1" />
            <div>
              <div class="mode-title">第 {{ n }} 个角色图</div>
            </div>
          </label>
        </div>
        <div class="batch-actions">
          <button class="action-btn" @click="roleDialog.visible = false">取消</button>
          <button class="action-btn primary" @click="applyBatchRoleImage">应用</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onActivated, onDeactivated, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useToast } from '../composables/toast.js'

const route = useRoute()
const toast = useToast()
const loading = ref(false)
const project = ref({})
const items = ref([])
const dialogItem = ref(null)
const mainBatchDialog = reactive({ visible: false, index: 1 })
const roleDialog = reactive({ visible: false, index: 0 })
const batchDialog = reactive({
  visible: false,
  type: 'image',
  mode: 'missing',
  total: 0,
  missing: 0,
})

const IDLE_STATUS = '待处理'
const IMAGE_QUEUED_STATUS = '图片排队中'
const IMAGE_RUNNING_STATUS = '图片生成中'
const IMAGE_DONE_STATUS = '图片生成完成'
const VIDEO_QUEUED_STATUS = '视频排队中'
const VIDEO_RUNNING_STATUS = '视频生成中'
const VIDEO_DONE_STATUS = '视频生成完成'
const IMAGE_ACTIVE_STATUSES = new Set([IMAGE_QUEUED_STATUS, IMAGE_RUNNING_STATUS])
const VIDEO_ACTIVE_STATUSES = new Set([VIDEO_QUEUED_STATUS, VIDEO_RUNNING_STATUS])
const RUNNING_STATUSES = new Set([...IMAGE_ACTIVE_STATUSES, ...VIDEO_ACTIVE_STATUSES])
const RUNNING_MAP = { '生图中': IMAGE_RUNNING_STATUS, '生视频中': VIDEO_RUNNING_STATUS }

function deriveImageStatus({ hasRoleImages, prevStatus = '', backendRunning = '' }) {
  if (backendRunning === IMAGE_RUNNING_STATUS) return IMAGE_RUNNING_STATUS
  if (hasRoleImages) return IMAGE_DONE_STATUS
  if ((prevStatus === IMAGE_QUEUED_STATUS || prevStatus === IMAGE_RUNNING_STATUS) && !backendRunning) return prevStatus
  return IDLE_STATUS
}

function deriveVideoStatus({ hasVideo, prevStatus = '', backendRunning = '' }) {
  if (backendRunning === VIDEO_RUNNING_STATUS) return VIDEO_RUNNING_STATUS
  if (hasVideo) return VIDEO_DONE_STATUS
  if ((prevStatus === VIDEO_QUEUED_STATUS || prevStatus === VIDEO_RUNNING_STATUS) && !backendRunning) return prevStatus
  return IDLE_STATUS
}

function settledImageStatus(roleImages) {
  return Array.isArray(roleImages) && roleImages.length ? IMAGE_DONE_STATUS : IDLE_STATUS
}

function settledVideoStatus(videoUrl) {
  return videoUrl ? VIDEO_DONE_STATUS : IDLE_STATUS
}

function isItemBusy(item) {
  return RUNNING_STATUSES.has(item.image_status) || RUNNING_STATUSES.has(item.video_status)
}

function imageButtonLabel(item) {
  return IMAGE_ACTIVE_STATUSES.has(item.image_status) ? item.image_status : '图片生成'
}

function videoButtonLabel(item) {
  return VIDEO_ACTIVE_STATUSES.has(item.video_status) ? item.video_status : '视频生成'
}

async function loadWorkspace(silent = false) {
  if (!silent) loading.value = true
  try {
    const api = await waitForApi()
    const projectId = decodeURIComponent(String(route.params.projectId || ''))
    const result = await api.list_project_items(projectId)
    if (result?.ok) {
      project.value = result.project || {}
      // 保留运行时状态
      const prevStatus = Object.fromEntries(items.value.map(i => [i.product_id, {
        image_status: i.image_status,
        video_status: i.video_status,
      }]))
      const prevSelections = Object.fromEntries(items.value.map(i => [i.product_id, {
        selected_role_index: i.selected_role_index,
        main_image_index: i.main_image_index,
      }]))
      items.value = (result.items || []).map((item) => {
        const assetVersion = Date.now()
        const roleImages = Array.isArray(item.role_images) ? item.role_images.slice(0, 4).map(path => toFileUrl(path, assetVersion)) : []
        const videoUrl = item.video_url ? toFileUrl(item.video_url, assetVersion) : ''
        const prev = prevStatus[item.product_id] || {}
        const backendRunning = RUNNING_MAP[item.running] || ''
        const imageStatus = deriveImageStatus({
          hasRoleImages: roleImages.length > 0,
          prevStatus: prev.image_status,
          backendRunning,
        })
        const videoStatus = deriveVideoStatus({
          hasVideo: Boolean(videoUrl),
          prevStatus: prev.video_status,
          backendRunning,
        })
        const sel = prevSelections[item.product_id] || {}
        const mainIdx = sel.main_image_index ?? 0
        return {
          ...item,
          product_images: Array.isArray(item.product_images) ? item.product_images : [],
          main_image_index: mainIdx,
          main_image_url: resolveMainImageUrl(item, mainIdx),
          role_images: roleImages,
          selected_role_index: sel.selected_role_index ?? 0,
          video_url: videoUrl,
          image_status: imageStatus,
          video_status: videoStatus,
        }
      })
      if (!silent) dialogItem.value = null
    } else if (!silent) {
      toast.error(result?.message || '工作台加载失败')
    }
  } catch (error) {
    if (!silent) toast.error('工作台加载失败：' + error)
  } finally {
    if (!silent) loading.value = false
  }
}

let autoRefreshTimer = null
const preview = ref({ visible: false, url: '', type: 'image' })

function closeTransientUi() {
  dialogItem.value = null
  preview.value = { visible: false, url: '', type: 'image' }
  batchDialog.visible = false
  mainBatchDialog.visible = false
  roleDialog.visible = false
}

function startAutoRefresh() {
  stopAutoRefresh()
  autoRefreshTimer = setInterval(() => loadWorkspace(true), 10000)
}

function stopAutoRefresh() {
  if (!autoRefreshTimer) return
  clearInterval(autoRefreshTimer)
  autoRefreshTimer = null
}

watch(
  () => route.params.projectId,
  () => {
    closeTransientUi()
    loadWorkspace()
    startAutoRefresh()
  },
  { immediate: true },
)

onActivated(() => {
  startAutoRefresh()
})

onDeactivated(() => {
  stopAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})

async function waitForApi(retries = 20, delay = 200) {
  for (let i = 0; i < retries; i += 1) {
    const api = window.pywebview?.api
    if (api?.list_project_items) return api
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

function openMainBatchDialog() {
  mainBatchDialog.visible = true
}

function confirmMainBatch() {
  const position = mainBatchDialog.index
  items.value = items.value.map((item) => {
    const nextIndex = clampImageIndex(item.product_images, position - 1)
    return { ...item, main_image_index: nextIndex, main_image_url: resolveMainImageUrl(item, nextIndex) }
  })
  mainBatchDialog.visible = false
  toast.success(`已批量选择第 ${position} 张主图`)
}

function openMainImageDialog(item) {
  dialogItem.value = item
}

function closeMainImageDialog() {
  dialogItem.value = null
}

function selectMainImage(productId, index) {
  items.value = items.value.map((item) => {
    if (item.product_id !== productId) return item
    const nextIndex = clampImageIndex(item.product_images, index)
    return {
      ...item,
      main_image_index: nextIndex,
      main_image_url: resolveMainImageUrl(item, nextIndex),
    }
  })
  dialogItem.value = null
  toast.success(`已选择第 ${index + 1} 张主图`)
}

function openPreview(url, type = 'image') {
  if (!url) return
  preview.value = { visible: true, url, type }
}

function selectRoleImage(item, index) {
  items.value = items.value.map(i => i.product_id === item.product_id
    ? { ...i, selected_role_index: index } : i)
}

function openRoleDialog() {
  roleDialog.visible = true
}

function statusClass(status) {
  if (!status) return ''
  if (status.includes('完成')) return 'ok'
  if (status.includes('失败')) return 'fail'
  if (status.includes('中')) return 'running'
  return ''
}

function applyBatchRoleImage() {
  items.value = items.value.map((item) => ({ ...item, selected_role_index: roleDialog.index }))
  roleDialog.visible = false
  toast.success(`已批量选择第 ${roleDialog.index + 1} 个角色图`)
}

function clampImageIndex(images, desiredIndex) {
  if (!Array.isArray(images) || !images.length) return 0
  return Math.min(Math.max(desiredIndex, 0), images.length - 1)
}

function resolveMainImageUrl(item, index) {
  const images = Array.isArray(item.product_images) ? item.product_images : []
  if (images.length) {
    return toFileUrl(images[clampImageIndex(images, index)])
  }
  return item.image_url || ''
}

function appendVersion(url, version = '') {
  if (!version) return url
  return `${url}${url.includes('?') ? '&' : '?'}v=${version}`
}

function toFileUrl(path, version = '') {
  if (!path) return ''
  const raw = String(path)
  if (raw.startsWith('http://') || raw.startsWith('https://')) {
    return raw
  }
  if (raw.startsWith('file://')) {
    try {
      return appendVersion(new URL(raw).toString(), version)
    } catch {
      return appendVersion(raw, version)
    }
  }

  const normalized = raw.replace(/\\/g, '/')
  let fileUrl = ''
  if (/^[A-Za-z]:\//.test(normalized)) {
    fileUrl = `file:///${normalized}`
  } else if (normalized.startsWith('//')) {
    fileUrl = `file:${normalized}`
  } else if (normalized.startsWith('/')) {
    fileUrl = `file://${normalized}`
  } else {
    fileUrl = `file:///${normalized}`
  }

  return appendVersion(encodeURI(fileUrl), version)
}

function stripLocalFileUrl(path) {
  if (!path) return ''
  const raw = String(path)
  if (!raw.startsWith('file://')) return raw
  try {
    const url = new URL(raw)
    let pathname = decodeURIComponent(url.pathname || '')
    if (/^\/[A-Za-z]:\//.test(pathname)) {
      pathname = pathname.slice(1)
    }
    return url.host ? `//${url.host}${pathname}` : pathname
  } catch {
    return decodeURIComponent(raw.replace('file://', '').split('?')[0]).replace(/^\/([A-Za-z]:\/)/, '$1')
  }
}

async function handleGenerateImage(item) {
  if (!item.main_image_url) return toast.error('请先选择主图')
  items.value = items.value.map(i => i.product_id === item.product_id ? { ...i, image_status: IMAGE_RUNNING_STATUS } : i)
  try {
    const prompts = await window.pywebview.api.get_settings('prompts')
    const r = await window.pywebview.api.generate_image_task({
      product_id: item.product_id,
      main_image_path: item.product_images?.[item.main_image_index] || '',
      title: item.title,
      prompt: prompts?.image_prompt || '',
      project_dir: project.value.path || '',
    })
    if (r.ok) {
      const assetVersion = Date.now()
      const rolePaths = (r.parts || []).map(p => toFileUrl(p.path, assetVersion))
      items.value = items.value.map(i => i.product_id === item.product_id
        ? {
            ...i,
            role_images: rolePaths,
            video_url: '',
            image_status: settledImageStatus(rolePaths),
            video_status: settledVideoStatus(''),
          }
        : i)
      toast.success('生图完成')
    } else {
      items.value = items.value.map(i => i.product_id === item.product_id
        ? { ...i, image_status: settledImageStatus(i.role_images) }
        : i)
      toast.error(r.message || '生图失败')
    }
  } catch (e) {
    items.value = items.value.map(i => i.product_id === item.product_id
      ? { ...i, image_status: settledImageStatus(i.role_images) }
      : i)
    toast.error('生图失败：' + e)
  }
}

async function handleGenerateVideo(item) {
  const roleImg = item.role_images?.[item.selected_role_index]
  if (!roleImg) return toast.error('请先选择角色图')
  items.value = items.value.map(i => i.product_id === item.product_id ? { ...i, video_status: VIDEO_RUNNING_STATUS } : i)
  try {
    const prompts = await window.pywebview.api.get_settings('prompts')
    const r = await window.pywebview.api.generate_video_task({
      product_id: item.product_id,
      role_image_path: stripLocalFileUrl(roleImg),
      prompt: prompts?.video_prompt || '',
      project_dir: project.value.path || '',
    })
    if (r.ok) {
      const videoUrl = toFileUrl(r.path, Date.now())
      items.value = items.value.map(i => i.product_id === item.product_id
        ? { ...i, video_url: videoUrl, video_status: settledVideoStatus(videoUrl) }
        : i)
      toast.success('视频生成完成')
    } else {
      items.value = items.value.map(i => i.product_id === item.product_id
        ? { ...i, video_status: settledVideoStatus(i.video_url) }
        : i)
      toast.error(r.message || '视频生成失败')
    }
  } catch (e) {
    items.value = items.value.map(i => i.product_id === item.product_id
      ? { ...i, video_status: settledVideoStatus(i.video_url) }
      : i)
    toast.error('视频生成失败：' + e)
  }
}

function openBatchDialog(type) {
  batchDialog.type = type
  batchDialog.mode = 'missing'
  batchDialog.total = items.value.length
  batchDialog.missing = type === 'image' ? countMissingImageItems() : countMissingVideoItems()
  batchDialog.visible = true
}

function closeBatchDialog() {
  batchDialog.visible = false
}

function countMissingImageItems() {
  return items.value.filter((item) => !Array.isArray(item.role_images) || item.role_images.length < 4).length
}

function countMissingVideoItems() {
  return items.value.filter((item) => !item.video_url).length
}

async function confirmBatchAction() {
  const isImage = batchDialog.type === 'image'
  const prompts = await window.pywebview.api.get_settings('prompts')
  const allItems = batchDialog.mode === 'missing'
    ? items.value.filter(i => isImage ? (!i.role_images?.length) : !i.video_url)
    : items.value

  closeBatchDialog()

  const pids = new Set(allItems.map(i => i.product_id))
  items.value = items.value.map(i => pids.has(i.product_id)
    ? {
        ...i,
        image_status: isImage ? IMAGE_QUEUED_STATUS : i.image_status,
        video_status: isImage ? i.video_status : VIDEO_QUEUED_STATUS,
      }
    : i)

  toast.success(`开始批量${isImage ? '生图' : '生视频'}，共 ${allItems.length} 条`)

  if (isImage) {
    const payload = allItems.map(i => ({
      product_id: i.product_id,
      main_image_path: i.product_images?.[i.main_image_index] || '',
      title: i.title,
      prompt: prompts?.image_prompt || '',
      project_dir: project.value.path || '',
    }))
    await window.pywebview.api.batch_generate_image({ items: payload })
  } else {
    const payload = allItems.map(i => ({
      product_id: i.product_id,
      role_image_path: stripLocalFileUrl(i.role_images?.[i.selected_role_index] || ''),
      prompt: prompts?.video_prompt || '',
      project_dir: project.value.path || '',
    })).filter(i => i.role_image_path)
    await window.pywebview.api.batch_generate_video({ items: payload })
  }
}
</script>

<style scoped>
.page { padding: 32px; }
.page-header {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}
.back-link {
  display: inline-block;
  margin-bottom: 10px;
  background: transparent;
  border: none;
  padding: 0;
  font-size: 12px;
  color: #71717a;
  cursor: pointer;
}
.page-title { font-size: 22px; font-weight: 700; color: #18181b; letter-spacing: -0.6px; }
.page-desc { margin-top: 6px; font-size: 13px; color: #71717a; }
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}
.batch-picker {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.batch-label {
  font-size: 12px;
  color: #71717a;
  margin-right: 4px;
}
.batch-btn {
  width: 30px;
  height: 30px;
  border-radius: 999px;
  border: 1px solid #d4d4d8;
  background: #fff;
  color: #18181b;
  font-size: 12px;
  cursor: pointer;
}
.toolbar-btn {
  padding: 9px 14px;
  border-radius: 999px;
  border: 1px solid #d4d4d8;
  background: #fff;
  color: #18181b;
  font-size: 12px;
  cursor: pointer;
}
.toolbar-btn.primary {
  background: #18181b;
  border-color: #18181b;
  color: #fff;
}
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
.table-wrap {
  border: 1px solid #e4e4e7;
  border-radius: 18px;
  overflow: auto;
  background: #fff;
}
.workspace-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  min-width: 1180px;
}
.workspace-table th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: #f7f7f8;
  color: #52525b;
  font-size: 12px;
  font-weight: 600;
  text-align: left;
  padding: 14px 16px;
  border-bottom: 1px solid #e4e4e7;
}
.workspace-table td {
  vertical-align: top;
  padding: 16px;
  border-bottom: 1px solid #f1f1f3;
}
.workspace-table tr:last-child td {
  border-bottom: none;
}
.main-col { width: 190px; }
.role-img-wrap { position: relative; }
.role-selected-badge {
  position: absolute;
  top: 6px;
  left: 6px;
  background: #6366f1;
  color: #fff;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
}
.detail-col { width: 260px; }
.roles-col { width: 720px; }
.video-col { width: 300px; }
.action-col { width: 150px; }
.ratio-media {
  width: 177px;
  aspect-ratio: 9 / 16;
  border-radius: 12px;
  object-fit: cover;
  flex-shrink: 0;
  background: #f4f4f5;
  border: 1px solid #ececf0;
}
.main-media {
  width: 177px;
}
.clickable {
  cursor: pointer;
}
.roles-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
.video-media {
  width: 177px;
}
.placeholder-card {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
  text-align: center;
  color: #a1a1aa;
  font-size: 11px;
  background:
    linear-gradient(135deg, rgba(24, 24, 27, 0.04), rgba(24, 24, 27, 0.08)),
    repeating-linear-gradient(
      -45deg,
      rgba(255, 255, 255, 0.45),
      rgba(255, 255, 255, 0.45) 8px,
      rgba(255, 255, 255, 0.1) 8px,
      rgba(255, 255, 255, 0.1) 16px
    );
}
.item-copy {
  min-width: 0;
}
.item-title {
  font-size: 13px;
  line-height: 1.55;
  color: #18181b;
  margin-bottom: 10px;
}
.item-meta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  font-size: 11px;
  color: #71717a;
}
.action-stack {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.action-btn {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #d4d4d8;
  background: #fff;
  color: #18181b;
  font-size: 12px;
  cursor: pointer;
}
.action-btn.primary {
  background: #18181b;
  border-color: #18181b;
  color: #fff;
}
.empty-card {
  background: linear-gradient(180deg, #ffffff 0%, #f7f7f8 100%);
  border: 1px solid #e4e4e7;
  border-radius: 18px;
  padding: 18px;
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
.modal-mask {
  position: fixed;
  inset: 0;
  z-index: 100;
  background: rgba(24, 24, 27, 0.36);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.modal-card {
  width: min(980px, 100%);
  max-height: 84vh;
  overflow: auto;
  background: #fff;
  border-radius: 20px;
  padding: 20px;
  box-shadow: 0 24px 60px rgba(24, 24, 27, 0.18);
}
.modal-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 16px;
}
.modal-title {
  font-size: 18px;
  font-weight: 700;
  color: #18181b;
}
.modal-desc {
  margin-top: 6px;
  font-size: 12px;
  color: #71717a;
}
.modal-close {
  border: 1px solid #d4d4d8;
  background: #fff;
  color: #18181b;
  border-radius: 999px;
  padding: 8px 14px;
  font-size: 12px;
  cursor: pointer;
}
.picker-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(132px, 1fr));
  gap: 12px;
}
.picker-card {
  border: 1px solid #e4e4e7;
  border-radius: 16px;
  background: #fff;
  padding: 10px;
  cursor: pointer;
}
.picker-card.active {
  border-color: #18181b;
  box-shadow: inset 0 0 0 1px #18181b;
}
.picker-image {
  width: 100%;
  aspect-ratio: 9 / 16;
  border-radius: 12px;
  object-fit: cover;
  display: block;
  margin-bottom: 8px;
}
.picker-index {
  display: block;
  font-size: 12px;
  color: #52525b;
  text-align: center;
}
.empty-picker {
  font-size: 13px;
  color: #71717a;
  padding: 12px 4px;
}
.batch-modal {
  width: min(620px, 100%);
}
.batch-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}
.stat-box {
  border: 1px solid #e4e4e7;
  border-radius: 14px;
  padding: 14px;
  background: #fafafa;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.stat-label {
  font-size: 12px;
  color: #71717a;
}
.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: #18181b;
}
.mode-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 18px;
}
.mode-card {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 14px;
  border: 1px solid #e4e4e7;
  border-radius: 14px;
  cursor: pointer;
}
.mode-title {
  font-size: 14px;
  font-weight: 600;
  color: #18181b;
}
.mode-desc {
  margin-top: 4px;
  font-size: 12px;
  color: #71717a;
}
.batch-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
.video-thumb { position: relative; display: inline-block; }
.play-icon {
  position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  font-size: 28px; color: #fff; text-shadow: 0 2px 8px rgba(0,0,0,0.5); pointer-events: none;
}
.preview-modal {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
.preview-media {
  max-width: 85vw;
  max-height: 85vh;
  border-radius: 12px;
  object-fit: contain;
}
.preview-close {
  position: absolute;
  top: -40px;
  right: 0;
}
.role-img-wrap { position: relative; cursor: pointer; }
.status-badge {
  display: inline-block; padding: 4px 8px; border-radius: 6px;
  font-size: 11px; background: #f4f4f5; color: #71717a;
}
.status-badge.ok { background: #dcfce7; color: #16a34a; }
.status-badge.fail { background: #fef2f2; color: #dc2626; }
.status-badge.running { background: #fef9c3; color: #ca8a04; }
@media (max-width: 900px) {
  .page-header {
    flex-direction: column;
  }
}
</style>
