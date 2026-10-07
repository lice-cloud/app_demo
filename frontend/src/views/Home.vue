<template>
  <div class="home">
    <el-card shadow="never">
      <template #header>
        <span>欢迎使用 app_demo</span>
      </template>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="应用版本">v{{ health.version || '加载中...' }}</el-descriptions-item>
        <el-descriptions-item label="运行平台">{{ health.platform || '-' }}</el-descriptions-item>
        <el-descriptions-item label="Python 版本">{{ health.python_version || '-' }}</el-descriptions-item>
        <el-descriptions-item label="后端状态">
          <el-tag :type="health.status === 'ok' ? 'success' : 'danger'">
            {{ health.status === 'ok' ? '正常' : '异常' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <el-button type="primary" :loading="loading" @click="loadHealth">
        刷新后端信息
      </el-button>
      <el-button type="success" @click="goUpdate">
        检查软件更新
      </el-button>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { healthApi, type HealthResult } from '../api/modules/health'

const router = useRouter()
const loading = ref(false)
const health = ref<Partial<HealthResult>>({})

async function loadHealth() {
  loading.value = true
  try {
    const result = await healthApi.check()
    health.value = result
  } catch (e) {
    ElMessage.error('无法连接后端服务')
  } finally {
    loading.value = false
  }
}

function goUpdate() {
  router.push('/settings/update')
}

onMounted(loadHealth)
</script>

<style scoped>
.home {
  padding: 16px;
}
</style>