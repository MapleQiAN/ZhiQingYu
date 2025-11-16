import { createApp } from 'vue'
import { createI18n } from 'vue-i18n'
import App from './App.vue'
import router from './router'
import { messages } from './i18n'

// 创建 i18n 实例
const i18n = createI18n({
  legacy: false,
  locale: localStorage.getItem('locale') || 'zh',
  fallbackLocale: 'en',
  messages,
})

const app = createApp(App)

app.use(router)
app.use(i18n)

app.mount('#app')

