<template>
  <el-dialog
    v-model="visible"
    :title="title"
    width="560px"
    :close-on-click-modal="false"
    :close-on-press-escape="!isUpdating"
    :show-close="!isUpdating"
    @closed="onClosed"
  >
    <!-- 待发现 / 更新日志 -->
    <div v-if="phase === 'idle'" class="update-notes">
      <div class="version-row">
        <span class="label">当前版本</span>
        <span class="value">v{{ currentVersion }}</span>
        <el-icon class="arrow"><Right /></el-icon>
        <span class="label">最新版本</span>
        <span class="value highlight">v{{ latestVersion }}</span>
      </div>
      <el-divider />
      <div class="notes-title">更新日志</div>
      <!-- Markdown 富文本渲染 -->
      <div class="markdown-body" v-html="renderedNotes"></div>
    </div>

    <!-- 更新中 -->
    <div v-else-if="isUpdating" class="update-progress">
      <el-progress
        :percentage="progressPercent"
        :stroke-width="14"
        striped
        striped-flow
      />
      <div class="progress-message">{{ message }}</div>
      <div v-if="bytesTotal > 0" class="bytes-info">
        {{ formatBytes(bytesDone) }} / {{ formatBytes(bytesTotal) }}
      </div>
    </div>

    <!-- 成功 / 就绪 -->
    <div v-else-if="phase === 'done' || phase === 'ready'" class="update-done">
      <el-result icon="success" :title="phase === 'done' ? '更新完成' : '更新已就绪'" sub-title="请重启应用以加载新版本" />
    </div>

    <!-- 失败 -->
    <div v-else-if="phase === 'error'" class="update-error">
      <el-result icon="error" title="更新失败" :sub-title="error || message" />
    </div>

    <template #footer>
      <div v-if="phase === 'idle'">
        <el-button @click="onLater">稍后</el-button>
        <el-button type="primary" @click="onApply">立即更新</el-button>
      </div>
      <div v-else-if="phase === 'done' || phase === 'ready'">
        <el-button type="primary" @click="onRestart">重启应用</el-button>
      </div>
      <div v-else-if="phase === 'error'">
        <el-button @click="onLater">关闭</el-button>
        <el-button type="primary" @click="onApply">重试</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'
import { useUpdateStore } from '../stores/update'

const store = useUpdateStore()
const {
  hasUpdate,
  currentVersion,
  latestVersion,
  releaseNotes,
  phase,
  percent,
  bytesDone,
  bytesTotal,
  message,
  error,
  updating,
  dialogVisible
} = storeToRefs(store)

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true
})

const visible = computed({
  get: () => dialogVisible.value,
  set: (v: boolean) => {
    dialogVisible.value = v
  }
})

const title = computed(() => {
  if (phase.value === 'idle') return `发现新版本 v${latestVersion.value}`
  if (phase.value === 'done') return '更新完成'
  if (phase.value === 'ready') return '更新已就绪'
  if (phase.value === 'error') return '更新失败'
  return '正在更新'
})

// Markdown 转 HTML 并做 XSS 清洗
const renderedNotes = computed(() => {
  const raw = releaseNotes.value || '暂无更新说明'
  const html = md.render(raw)
  return DOMPurify.sanitize(html)
})

const progressPercent = computed(() => Math.round(percent.value))
const isUpdating = computed(() =>
  ['checking', 'downloading', 'verifying', 'installing'].includes(phase.value)
)

function formatBytes(bytes: number): string {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let v = bytes
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024
    i++
  }
  return `${v.toFixed(i === 0 ? 0 : 1)} ${units[i]}`
}

async function onApply() {
  try {
    await store.apply()
  } catch (e) {
    ElMessage.error('启动更新失败')
  }
}

function onLater() {
  store.closeDialog()
  store.stopPolling()
}

async function onRestart() {
  await store.restart()
  ElMessage.info('请手动关闭并重新打开应用')
}

function onClosed() {
  // 对话框关闭时，如果不在更新中，重置 phase
  if (!isUpdating.value && phase.value !== 'done') {
    store.stopPolling()
  }
}

// 当检查到新版本时自动打开对话框
watch(hasUpdate, (v) => {
  if (v) {
    store.openDialog()
  }
})
</script>

<style scoped>
.version-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  font-size: 14px;
}

.version-row .label {
  color: #909399;
}

.version-row .value {
  font-weight: 600;
}

.version-row .value.highlight {
  color: #409eff;
}

.version-row .arrow {
  color: #c0c4cc;
}

.notes-title {
  font-weight: 600;
  margin-bottom: 8px;
}

.update-notes :deep(.markdown-body) {
  max-height: 300px;
  overflow-y: auto;
  font-size: 13px;
  line-height: 1.7;
  color: #303133;
}

.update-notes :deep(.markdown-body h1),
.update-notes :deep(.markdown-body h2),
.update-notes :deep(.markdown-body h3) {
  font-size: 15px;
  margin: 12px 0 6px;
}

.update-notes :deep(.markdown-body ul),
.update-notes :deep(.markdown-body ol) {
  padding-left: 20px;
  margin: 6px 0;
}

.update-notes :deep(.markdown-body code) {
  background: #f5f7fa;
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 12px;
}

.update-notes :deep(.markdown-body pre) {
  background: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
}

.update-notes :deep(.markdown-body a) {
  color: #409eff;
}

.update-progress {
  padding: 16px 0;
}

.progress-message {
  margin-top: 16px;
  text-align: center;
  color: #606266;
}

.bytes-info {
  margin-top: 8px;
  text-align: center;
  font-size: 12px;
  color: #909399;
}
</style>