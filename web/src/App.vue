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
  background-attachment: fixed;
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #4A4A4A;
  position: relative;
  overflow-x: hidden;
}

body::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 50%, rgba(255, 182, 193, 0.08) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(255, 218, 185, 0.06) 0%, transparent 50%),
    radial-gradient(circle at 40% 20%, rgba(255, 192, 203, 0.05) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
}

#app {
  min-height: 100vh;
  position: relative;
  z-index: 1;
}

/* 优化滚动条样式 */
::-webkit-scrollbar {
  width: 12px;
  height: 12px;
}

::-webkit-scrollbar-track {
  background: rgba(255, 182, 193, 0.08);
  border-radius: 12px;
  border: 2px solid transparent;
  background-clip: padding-box;
}

::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, rgba(255, 182, 193, 0.4) 0%, rgba(255, 218, 185, 0.4) 100%);
  border-radius: 12px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  background-clip: padding-box;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, rgba(255, 182, 193, 0.6) 0%, rgba(255, 218, 185, 0.6) 100%);
  border-color: rgba(255, 255, 255, 0.3);
  box-shadow: 0 2px 8px rgba(255, 182, 193, 0.3);
}

::-webkit-scrollbar-thumb:active {
  background: linear-gradient(135deg, rgba(255, 182, 193, 0.7) 0%, rgba(255, 218, 185, 0.7) 100%);
}

/* 优化选择文本样式 */
::selection {
  background: linear-gradient(135deg, rgba(255, 182, 193, 0.35) 0%, rgba(255, 218, 185, 0.35) 100%);
  color: #8B6F7E;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.3);
}

::-moz-selection {
  background: linear-gradient(135deg, rgba(255, 182, 193, 0.35) 0%, rgba(255, 218, 185, 0.35) 100%);
  color: #8B6F7E;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.3);
}

/* 优化焦点样式 - 移除默认outline，使用自定义样式 */
*:focus-visible {
  outline: none !important;
  outline-offset: 0 !important;
}

/* 优化输入框样式 */
input, textarea {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  outline: none !important;
}

input:focus, textarea:focus {
  outline: none !important;
  box-shadow: 0 0 0 3px rgba(255, 182, 193, 0.15);
}

/* 移除所有元素的默认outline */
button:focus,
a:focus,
div:focus {
  outline: none !important;
}

/* 优化按钮点击效果 */
button {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

button:active {
  transform: scale(0.98);
}

/* ========== 全局移除 Naive UI 组件的绿色验证边框 ========== */

/* 覆盖所有输入组件的验证状态边框（成功/警告/错误状态） */
.n-input-wrapper--success .n-input__border,
.n-input-wrapper--success .n-input__state-border,
.n-input-wrapper--warning .n-input__border,
.n-input-wrapper--warning .n-input__state-border,
.n-input-wrapper--error .n-input__border,
.n-input-wrapper--error .n-input__state-border {
  border: none !important;
  border-color: transparent !important;
  box-shadow: none !important;
  display: none !important;
}

/* 覆盖聚焦时的验证状态边框 */
.n-input-wrapper--success.n-input-wrapper--focus .n-input__border,
.n-input-wrapper--success.n-input-wrapper--focus .n-input__state-border,
.n-input-wrapper--warning.n-input-wrapper--focus .n-input__border,
.n-input-wrapper--warning.n-input-wrapper--focus .n-input__state-border,
.n-input-wrapper--error.n-input-wrapper--focus .n-input__border,
.n-input-wrapper--error.n-input-wrapper--focus .n-input__state-border {
  border: none !important;
  border-color: transparent !important;
  box-shadow: none !important;
  display: none !important;
}

/* 覆盖所有输入组件的绿色 box-shadow */
.n-input-wrapper--success,
.n-input-wrapper--success *:not(.n-input__textarea-el),
.n-input-wrapper--warning,
.n-input-wrapper--warning *:not(.n-input__textarea-el),
.n-input-wrapper--error,
.n-input-wrapper--error *:not(.n-input__textarea-el) {
  box-shadow: none !important;
}

/* 覆盖聚焦时的 box-shadow（但不影响 textarea 本身） */
.n-input-wrapper--success.n-input-wrapper--focus,
.n-input-wrapper--success.n-input-wrapper--focus *:not(.n-input__textarea-el),
.n-input-wrapper--warning.n-input-wrapper--focus,
.n-input-wrapper--warning.n-input-wrapper--focus *:not(.n-input__textarea-el),
.n-input-wrapper--error.n-input-wrapper--focus,
.n-input-wrapper--error.n-input-wrapper--focus *:not(.n-input__textarea-el) {
  box-shadow: none !important;
}

/* 覆盖所有可能的伪元素边框 */
.n-input-wrapper--success::before,
.n-input-wrapper--success::after,
.n-input-wrapper--warning::before,
.n-input-wrapper--warning::after,
.n-input-wrapper--error::before,
.n-input-wrapper--error::after,
.n-input-wrapper--success.n-input-wrapper--focus::before,
.n-input-wrapper--success.n-input-wrapper--focus::after,
.n-input-wrapper--warning.n-input-wrapper--focus::before,
.n-input-wrapper--warning.n-input-wrapper--focus::after,
.n-input-wrapper--error.n-input-wrapper--focus::before,
.n-input-wrapper--error.n-input-wrapper--focus::after,
.n-input__border::before,
.n-input__border::after,
.n-input__state-border::before,
.n-input__state-border::after {
  border: none !important;
  border-color: transparent !important;
  box-shadow: none !important;
  display: none !important;
}

/* 覆盖按钮的验证状态边框 */
.n-button--success,
.n-button--success *,
.n-button__border--success,
.n-button--warning,
.n-button--warning *,
.n-button__border--warning,
.n-button--error,
.n-button--error *,
.n-button__border--error {
  border-color: transparent !important;
  box-shadow: none !important;
}

/* 覆盖选择器的验证状态边框 */
.n-select--success .n-base-selection,
.n-select--success .n-base-selection__border,
.n-select--warning .n-base-selection,
.n-select--warning .n-base-selection__border,
.n-select--error .n-base-selection,
.n-select--error .n-base-selection__border {
  border-color: transparent !important;
  box-shadow: none !important;
}

/* 覆盖日期选择器的验证状态边框 */
.n-date-picker--success .n-input-wrapper,
.n-date-picker--success .n-input__border,
.n-date-picker--warning .n-input-wrapper,
.n-date-picker--warning .n-input__border,
.n-date-picker--error .n-input-wrapper,
.n-date-picker--error .n-input__border {
  border-color: transparent !important;
  box-shadow: none !important;
}

/* 覆盖其他可能使用验证状态的组件 */
.n-form-item--success .n-input-wrapper,
.n-form-item--warning .n-input-wrapper,
.n-form-item--error .n-input-wrapper,
.n-form-item--success .n-select,
.n-form-item--warning .n-select,
.n-form-item--error .n-select {
  border-color: transparent !important;
  box-shadow: none !important;
}
</style>

