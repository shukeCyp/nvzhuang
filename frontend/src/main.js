import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import App from './App.vue'
import Home from './views/Home.vue'
import Crawler from './views/Crawler.vue'
import Debug from './views/Debug.vue'
import Settings from './views/Settings.vue'
import Workspace from './views/Workspace.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', component: Home },
    { path: '/workspace/:projectId', component: Workspace },
    { path: '/crawler', component: Crawler },
    { path: '/debug', component: Debug },
    { path: '/settings', component: Settings },
  ]
})

createApp(App).use(router).mount('#app')
