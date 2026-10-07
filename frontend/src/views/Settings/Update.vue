<template>
  <div class="update-settings">
    <el-card shadow="never">
      <template #header>
        <span>软件更新</span>
      </template>

      <div class="info-row">
        <span class="label">当前版本</span>
        <span class="value">v{{ currentVersion }}</span>
      </div>

      <div class="info-row">
        <span class="label">更新状态</span>
        <el-tag v-if="checking" type="info">检查中...</el-tag>
        <el-tag v-else-if="hasUpdate" type="warning">有新版本 v{{ latestVersion }}</el-tag>
        <el-tag v-else type="success">已是最新版本</el-tag>
      </div>

      <div class="actions">
        <el-button
          type="primary"
          :loading="checking"
          @click="onCheck"
        >
          检查更新
        </el-button>
        <el-button
          v-if="hasUpdate"
          type="success"
          @click="store.openDialog()"
        >
          查看更新
        </el-button>
      </div>
    </el-card>

    <!-- 更新对话框 -->
    <UpdateDialog />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { useUpdateStore } from '../../stores/update'
import UpdateDialog from '../../components/UpdateDialog.vue'

const store = useUpdateStore()
const { checking, hasUpdate, latestVersion, currentVersion } = storeToRefs(store)

async function onCheck() {
  try {
    const result = await store.check()
    if (result.has_update) {
      ElMessage.warning(`发现新版本 v${result.latest_version}`)
    } else {
      ElMessage.success('已是最新版本')
    }
  } catch (e) {
    ElMessage.error('检查更新失败，请检查网络连接')
  }
}

onMounted(async () => {
  // 页面加载时获取当前版本
  try {
    const result = await store.check()
    if (result.has_update) {
      store.openDialog()
    }
  } catch (e) {
    // 静默失败
  }
})
</script>

<style scoped>
.update-settings {
  padding: 16px;
}

.info-row {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.info-row .label {
  width: 100px;
  color: #909399;
}

.info-row .value {
  font-weight: 600;
}

.actions {
  margin-top: 24px;
}
</style>