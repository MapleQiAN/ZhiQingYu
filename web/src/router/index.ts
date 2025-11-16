import { createRouter, createWebHistory } from 'vue-router'
import Chat from '../views/Chat.vue'
import Journal from '../views/Journal.vue'
import Overview from '../views/Overview.vue'
import Settings from '../views/Settings.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Chat',
      component: Chat,
    },
    {
      path: '/journal',
      name: 'Journal',
      component: Journal,
    },
    {
      path: '/overview',
      name: 'Overview',
      component: Overview,
    },
    {
      path: '/settings',
      name: 'Settings',
      component: Settings,
    },
  ],
})

export default router

