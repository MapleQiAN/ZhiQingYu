<template>
  <n-config-provider :theme="theme" :locale="locale" :date-locale="dateLocale">
    <n-message-provider>
      <n-notification-provider>
        <n-dialog-provider>
          <Layout>
            <router-view />
          </Layout>
        </n-dialog-provider>
      </n-notification-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { NConfigProvider, NMessageProvider, NNotificationProvider, NDialogProvider, zhCN, enUS, dateZhCN, dateEnUS } from 'naive-ui'
import Layout from './components/Layout.vue'

const { locale: i18nLocale } = useI18n()

const theme = computed(() => null) // 使用默认主题

const locale = computed(() => {
  return i18nLocale.value === 'zh' ? zhCN : enUS
})

const dateLocale = computed(() => {
  return i18nLocale.value === 'zh' ? dateZhCN : dateEnUS
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  background: linear-gradient(135deg, #FFF9F5 0%, #FFF5ED 50%, #FFF0E6 100%);
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #4A4A4A;
}

#app {
  min-height: 100vh;
  position: relative;
}

/* 优化滚动条样式 */
::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

::-webkit-scrollbar-track {
  background: rgba(255, 182, 193, 0.05);
  border-radius: 10px;
}

::-webkit-scrollbar-thumb {
  background: rgba(255, 182, 193, 0.3);
  border-radius: 10px;
  transition: background 0.3s ease;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 182, 193, 0.5);
}

/* 优化选择文本样式 */
::selection {
  background: rgba(255, 182, 193, 0.3);
  color: #8B6F7E;
}

::-moz-selection {
  background: rgba(255, 182, 193, 0.3);
  color: #8B6F7E;
}
</style>

