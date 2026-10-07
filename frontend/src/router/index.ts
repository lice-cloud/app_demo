import { createRouter, createWebHashHistory } from 'vue-router'
import Home from '../views/Home.vue'

const router = createRouter({
  // 桌面应用使用 hash 模式，避免 file:// 协议下的路径问题
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home,
      meta: { title: '首页' }
    },
    {
      path: '/settings/update',
      name: 'settings-update',
      component: () => import('../views/Settings/Update.vue'),
      meta: { title: '软件更新' }
    }
  ]
})

export default router