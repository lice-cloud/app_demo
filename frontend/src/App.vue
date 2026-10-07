<template>
  <el-container class="app-container">
    <el-aside width="200px" class="app-aside">
      <div class="logo">app_demo</div>
      <el-menu :default-active="activeMenu" router>
        <el-menu-item index="/">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="/settings/update">
          <el-icon><Setting /></el-icon>
          <span>软件更新</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="app-header">
        <span>{{ pageTitle }}</span>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>

  <!-- 全局更新对话框 -->
  <UpdateDialog />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import UpdateDialog from './components/UpdateDialog.vue'

const route = useRoute()

const activeMenu = computed(() => route.path)
const pageTitle = computed(() => (route.meta.title as string) || 'app_demo')
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body,
#app {
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.app-container {
  height: 100%;
}

.app-aside {
  background: #fff;
  border-right: 1px solid #e6e6e6;
}

.logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  font-size: 18px;
  font-weight: 700;
  color: #409eff;
  border-bottom: 1px solid #e6e6e6;
}

.app-header {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
}
</style>