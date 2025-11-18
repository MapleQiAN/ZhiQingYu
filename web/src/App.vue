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
@import './styles/design-system.css';

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-family-base);
  font-size: var(--font-size-base);
  line-height: var(--line-height-normal);
  background: var(--bg-primary);
  background-image: 
    radial-gradient(circle at 20% 50%, rgba(232, 180, 184, 0.08) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(244, 194, 161, 0.06) 0%, transparent 50%),
    radial-gradient(circle at 40% 20%, rgba(232, 180, 184, 0.05) 0%, transparent 50%);
  background-attachment: fixed;
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--text-primary);
  position: relative;
  overflow-x: hidden;
}


#app {
  min-height: 100vh;
  position: relative;
  z-index: var(--z-base);
}

/* 优化滚动条样式 - 使用设计系统变量 */
::-webkit-scrollbar {
  width: 12px;
  height: 12px;
}

::-webkit-scrollbar-track {
  background: var(--color-neutral-100);
  border-radius: var(--radius-full);
  border: 2px solid transparent;
  background-clip: padding-box;
}

::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, var(--color-primary-light) 0%, var(--color-secondary-light) 100%);
  border-radius: var(--radius-full);
  border: 2px solid rgba(255, 255, 255, 0.2);
  background-clip: padding-box;
  transition: all var(--transition-base);
}

::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  border-color: rgba(255, 255, 255, 0.3);
  box-shadow: var(--shadow-warm-sm);
}

::-webkit-scrollbar-thumb:active {
  background: linear-gradient(135deg, var(--color-primary-dark) 0%, var(--color-secondary) 100%);
}

/* 优化选择文本样式 - 使用设计系统变量 */
::selection {
  background: linear-gradient(135deg, var(--color-primary-light) 0%, var(--color-secondary-light) 100%);
  color: var(--text-primary);
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.3);
}

::-moz-selection {
  background: linear-gradient(135deg, var(--color-primary-light) 0%, var(--color-secondary-light) 100%);
  color: var(--text-primary);
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.3);
}

/* 优化焦点样式 - 移除默认outline，使用自定义样式 */
*:focus-visible {
  outline: none !important;
  outline-offset: 0 !important;
}

/* 优化输入框样式 - 使用设计系统变量 */
input, textarea {
  transition: all var(--transition-base);
  outline: none !important;
}

input:focus, textarea:focus {
  outline: none !important;
  box-shadow: 0 0 0 3px var(--color-primary-lighter);
}

/* 移除所有元素的默认outline */
button:focus,
a:focus,
div:focus {
  outline: none !important;
}

/* 优化按钮点击效果 - 使用设计系统变量 */
button {
  transition: all var(--transition-fast);
  cursor: pointer;
}

button:active {
  transform: scale(0.98);
}

button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

/* 优化链接样式 - 使用设计系统变量 */
a {
  transition: all var(--transition-fast);
  text-decoration: none;
  color: var(--color-primary);
}

a:hover {
  opacity: 0.8;
  color: var(--color-primary-dark);
}

/* 优化图片加载效果 */
img {
  transition: opacity 0.3s ease;
}

img[loading] {
  opacity: 0;
}

/* 优化卡片悬停效果 - 使用设计系统变量 */
.n-card {
  transition: all var(--transition-base);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.n-card:hover {
  box-shadow: var(--shadow-md);
}

/* ========== 全局优化弹窗和按钮圆角 - 更圆润 ========== */

/* 弹窗（Dialog/Modal）圆角优化 - 覆盖所有可能的类名 */
.n-modal,
.n-modal .n-card,
.n-modal__content,
.n-modal__content-wrapper,
.n-dialog,
.n-dialog .n-card,
[class*="n-modal"],
[class*="n-dialog"] {
  border-radius: var(--radius-2xl) !important;
}

.n-modal .n-card-body,
.n-dialog .n-card-body,
.n-modal .n-card__content,
.n-dialog .n-card__content {
  border-radius: var(--radius-2xl) !important;
}

/* 按钮（Button）圆角优化 - 覆盖所有按钮相关元素 */
.n-button,
.n-button__border,
.n-button__state-border,
.n-button .n-button__border,
button.n-button,
[class*="n-button"]:not([class*="__icon"]):not([class*="__loading"]) {
  border-radius: var(--radius-lg) !important;
}

/* 小尺寸按钮使用中等圆角 */
.n-button--tiny,
.n-button--tiny .n-button__border,
.n-button--small,
.n-button--small .n-button__border {
  border-radius: var(--radius-md) !important;
}

/* 大尺寸按钮使用更大圆角 */
.n-button--large,
.n-button--large .n-button__border,
.n-button--huge,
.n-button--huge .n-button__border {
  border-radius: var(--radius-xl) !important;
}

/* 确保按钮内部元素也继承圆角 */
.n-button > * {
  border-radius: inherit;
}

/* 优化加载动画 - 使用设计系统变量 */
@keyframes shimmer {
  0% {
    background-position: -1000px 0;
  }
  100% {
    background-position: 1000px 0;
  }
}

.loading-shimmer {
  animation: shimmer 2s infinite linear;
  background: linear-gradient(
    to right,
    var(--color-primary-lighter) 0%,
    var(--color-primary-light) 50%,
    var(--color-primary-lighter) 100%
  );
  background-size: 1000px 100%;
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

