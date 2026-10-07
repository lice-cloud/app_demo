import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { updateApi, type UpdateStatus } from '../api/modules/update'

export const useUpdateStore = defineStore('update', () => {
  // 状态
  const checking = ref(false)
  const hasUpdate = ref(false)
  const currentVersion = ref('')
  const latestVersion = ref<string | null>(null)
  const releaseNotes = ref<string | null>(null)
  const releaseUrl = ref<string | null>(null)

  const phase = ref<UpdateStatus['phase']>('idle')
  const percent = ref(0)
  const bytesDone = ref(0)
  const bytesTotal = ref(0)
  const message = ref('')
  const error = ref<string | null>(null)
  const updating = ref(false)
  const dialogVisible = ref(false)

  let pollTimer: ReturnType<typeof setInterval> | null = null

  // 计算属性
  const progressPercent = computed(() => Math.round(percent.value))
  const isUpdating = computed(() =>
    ['checking', 'downloading', 'verifying', 'installing'].includes(phase.value)
  )
  const canRestart = computed(() => phase.value === 'done' || phase.value === 'ready')

  // 检查更新
  async function check() {
    checking.value = true
    error.value = null
    try {
      const result = await updateApi.check()
      currentVersion.value = result.current_version
      hasUpdate.value = result.has_update
      latestVersion.value = result.latest_version ?? null
      releaseNotes.value = result.notes ?? null
      releaseUrl.value = result.release_url ?? null
      return result
    } catch (e: any) {
      error.value = e?.message || '检查更新失败'
      hasUpdate.value = false
      throw e
    } finally {
      checking.value = false
    }
  }

  // 执行更新
  async function apply() {
    updating.value = true
    error.value = null
    try {
      const result = await updateApi.apply()
      if (result.task_started) {
        startPolling()
      } else {
        message.value = result.message
      }
      return result
    } catch (e: any) {
      error.value = e?.message || '启动更新失败'
      updating.value = false
      throw e
    }
  }

  // 轮询状态
  function startPolling() {
    stopPolling()
    pollTimer = setInterval(async () => {
      try {
        const status = await updateApi.status()
        phase.value = status.phase
        percent.value = status.percent
        bytesDone.value = status.bytes_done
        bytesTotal.value = status.bytes_total
        message.value = status.message
        error.value = status.error ?? null

        if (status.phase === 'done' || status.phase === 'error' || status.phase === 'ready') {
          stopPolling()
          updating.value = false
        }
      } catch (e: any) {
        console.error('[Update] poll error', e)
      }
    }, 600)
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  // 重启
  async function restart() {
    try {
      await updateApi.restart()
    } catch (e) {
      console.error('[Update] restart error', e)
    }
  }

  function openDialog() {
    dialogVisible.value = true
  }

  function closeDialog() {
    dialogVisible.value = false
  }

  return {
    checking,
    hasUpdate,
    currentVersion,
    latestVersion,
    releaseNotes,
    releaseUrl,
    phase,
    percent,
    bytesDone,
    bytesTotal,
    message,
    error,
    updating,
    dialogVisible,
    progressPercent,
    isUpdating,
    canRestart,
    check,
    apply,
    restart,
    startPolling,
    stopPolling,
    openDialog,
    closeDialog
  }
})