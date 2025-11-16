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
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background-color: #f5f5f5;
}

#app {
  min-height: 100vh;
}
</style>

