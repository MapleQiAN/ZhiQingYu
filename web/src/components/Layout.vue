<template>
  <div class="min-h-screen warm-bg">
    <n-layout>
      <n-layout-header bordered class="warm-header">
        <div class="header-container">
          <div class="header-content">
            <div class="logo-section group cursor-pointer" @click="router.push('/')">
              <div class="app-logo-wrapper">
                <img src="../logo/logo.png" alt="Logo" class="app-logo" />
                <div class="logo-glow"></div>
              </div>
              <div class="title-wrapper">
                <h1 class="app-title">
                  {{ $t('common.appName') }}
                </h1>
                <div class="title-underline"></div>
              </div>
            </div>
            <div class="nav-section">
              <n-menu
                mode="horizontal"
                :value="activeKey"
                :options="menuOptions"
                @update:value="handleMenuSelect"
                class="warm-menu"
              />
              <div class="divider"></div>
              <n-dropdown
                trigger="click"
                :options="localeOptions"
                @select="handleLocaleSelect"
                placement="bottom-end"
                :value="currentLocale"
              >
                <n-button
                  quaternary
                  circle
                  size="medium"
                  class="locale-button"
                  :title="$t('nav.language')"
                >
                  <template #icon>
                    <span class="locale-icon">{{ currentLocale === 'zh' ? '🇨🇳' : '🇺🇸' }}</span>
                  </template>
                </n-button>
              </n-dropdown>
              <n-button
                quaternary
                circle
                size="medium"
                class="settings-button"
                @click="router.push('/settings')"
                :title="$t('nav.settings')"
              >
                <template #icon>
                  <span class="settings-icon">⚙️</span>
                </template>
              </n-button>
            </div>
          </div>
          <div class="header-decoration"></div>
        </div>
      </n-layout-header>
      <n-layout-content>
        <div class="content-wrapper">
          <slot />
        </div>
      </n-layout-content>
    </n-layout>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  NLayout,
  NLayoutHeader,
  NLayoutContent,
  NMenu,
  NButton,
  NDropdown,
} from 'naive-ui'
import type { MenuOption, DropdownOption } from 'naive-ui'

const router = useRouter()
const route = useRoute()
const { locale, t } = useI18n()

const currentLocale = ref(locale.value)

// 同步 locale 变化
watch(() => locale.value, (newLocale) => {
  currentLocale.value = newLocale
})

const menuOptions = computed<MenuOption[]>(() => [
  {
    label: t('nav.chat'),
    key: '/',
  },
  {
    label: t('nav.journal'),
    key: '/journal',
  },
  {
    label: t('nav.overview'),
    key: '/overview',
  },
])

const localeOptions = computed<DropdownOption[]>(() => {
  const labels = {
    zh: '中文',
    en: 'English',
  }
  return [
    {
      label: () => h('span', { style: 'display: flex; align-items: center; gap: 8px;' }, [
        h('span', { style: 'font-size: 18px;' }, '🇨🇳'),
        h('span', labels.zh),
      ]),
      key: 'zh',
    },
    {
      label: () => h('span', { style: 'display: flex; align-items: center; gap: 8px;' }, [
        h('span', { style: 'font-size: 18px;' }, '🇺🇸'),
        h('span', labels.en),
      ]),
      key: 'en',
    },
  ]
})

const activeKey = computed(() => {
  const path = route.path
  // 确保路径匹配菜单项的 key
  if (path === '/' || path.startsWith('/chat')) {
    return '/'
  }
  return path
})

const handleMenuSelect = (key: string) => {
  router.push(key)
}

const handleLocaleSelect = (key: string | number) => {
  const newLocale = key as string
  currentLocale.value = newLocale
  locale.value = newLocale
  localStorage.setItem('locale', newLocale)
}
</script>

<style scoped>
@import '../styles/design-system.css';

.warm-bg {
  background: var(--bg-primary);
  background-image: 
    radial-gradient(circle at 20% 50%, rgba(232, 180, 184, 0.08) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(244, 194, 161, 0.06) 0%, transparent 50%);
  min-height: 100vh;
  position: relative;
}

.warm-header {
  background: rgba(255, 255, 255, 0.9) !important;
  backdrop-filter: blur(25px) saturate(180%);
  -webkit-backdrop-filter: blur(25px) saturate(180%);
  box-shadow: var(--shadow-warm-md);
  border-bottom: var(--border-width-thin) solid var(--border-color-light) !important;
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
  transition: all var(--transition-smooth);
  overflow: hidden;
}

.warm-header:hover {
  box-shadow: var(--shadow-warm-lg);
  border-bottom-color: var(--border-color-base) !important;
}

.header-container {
  position: relative;
  width: 100%;
  margin: 0;
  padding: 0 var(--spacing-xl);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg) 0;
  position: relative;
  z-index: var(--z-elevated);
}

.logo-section {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  transition: transform var(--transition-base);
  position: relative;
}

.logo-section:hover {
  transform: translateX(2px);
}

.app-logo-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.app-logo {
  width: 48px;
  height: 48px;
  object-fit: contain;
  filter: drop-shadow(0 3px 6px rgba(232, 180, 184, 0.4));
  transition: all var(--transition-smooth);
  position: relative;
  z-index: var(--z-elevated);
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
  }
  50% {
    transform: translateY(-4px) rotate(5deg);
  }
}

.logo-section:hover .app-logo {
  transform: rotate(15deg) scale(1.15);
  filter: drop-shadow(0 4px 8px rgba(255, 182, 193, 0.5));
}

.logo-glow {
  position: absolute;
  width: 50px;
  height: 50px;
  border-radius: var(--radius-full);
  background: radial-gradient(circle, var(--color-primary-light) 0%, transparent 70%);
  opacity: 0;
  transition: opacity var(--transition-base);
  z-index: var(--z-base);
}

.logo-section:hover .logo-glow {
  opacity: 1;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 0.4;
  }
  50% {
    transform: scale(1.2);
    opacity: 0.6;
  }
}

.title-wrapper {
  position: relative;
  display: flex;
  flex-direction: column;
}

.app-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  background: linear-gradient(135deg, var(--color-primary-darker) 0%, var(--color-primary-dark) 50%, var(--color-primary) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 0.8px;
  margin: 0;
  line-height: var(--line-height-tight);
  transition: all var(--transition-base);
  position: relative;
}

.logo-section:hover .app-title {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-darker) 50%, var(--color-primary-dark) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  transform: translateX(2px);
}

.title-underline {
  height: 3px;
  width: 0;
  background: linear-gradient(90deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  border-radius: var(--radius-xs);
  transition: width var(--transition-smooth);
  margin-top: var(--spacing-xs);
}

.logo-section:hover .title-underline {
  width: 100%;
}

.nav-section {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
}

.divider {
  width: var(--border-width-thin);
  height: 24px;
  background: linear-gradient(180deg, transparent 0%, var(--border-color-base) 50%, transparent 100%);
}

.warm-menu {
  background: transparent !important;
}

.warm-menu :deep(.n-menu) {
  background: transparent !important;
}

.warm-menu :deep(.n-menu-item) {
  color: var(--text-secondary);
  transition: all var(--transition-base);
  font-weight: var(--font-weight-medium);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-lg);
  margin: 0 var(--spacing-xs);
  position: relative;
  overflow: hidden;
}

.warm-menu :deep(.n-menu-item::before) {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s ease;
}

.warm-menu :deep(.n-menu-item:hover::before) {
  left: 100%;
}

.warm-menu :deep(.n-menu-item--selected) {
  color: var(--color-primary-darker) !important;
  background: linear-gradient(135deg, var(--color-primary-lighter) 0%, var(--color-secondary-lighter) 100%) !important;
  font-weight: var(--font-weight-semibold);
  box-shadow: var(--shadow-warm-sm);
  transform: translateY(-1px);
}

.warm-menu :deep(.n-menu-item--selected::after) {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 60%;
  height: 2px;
  background: linear-gradient(90deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  border-radius: var(--radius-xs);
}

.warm-menu :deep(.n-menu-item:hover) {
  color: var(--color-primary-darker);
  background: linear-gradient(135deg, var(--color-primary-lighter) 0%, var(--color-secondary-lighter) 100%);
  transform: translateY(-2px);
  box-shadow: var(--shadow-warm-sm);
}

.warm-menu :deep(.n-menu-item:active) {
  transform: translateY(0);
  box-shadow: 0 1px 4px rgba(255, 182, 193, 0.1);
}

.locale-button,
.settings-button {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full) !important;
  background: rgba(255, 255, 255, 0.6) !important;
  backdrop-filter: blur(10px);
  border: var(--border-width-thin) solid var(--border-color-light) !important;
  transition: all var(--transition-base);
  box-shadow: var(--shadow-sm);
  display: flex;
  align-items: center;
  justify-content: center;
}

.locale-button:hover,
.settings-button:hover {
  background: rgba(255, 255, 255, 0.8) !important;
  border-color: var(--border-color-base) !important;
  box-shadow: var(--shadow-warm-md);
  transform: translateY(-2px) scale(1.05);
}

.locale-icon,
.settings-icon {
  font-size: var(--font-size-xl);
  line-height: var(--line-height-tight);
  filter: drop-shadow(0 2px 4px rgba(232, 180, 184, 0.3));
  transition: transform var(--transition-base);
}

.locale-button:hover .locale-icon,
.settings-button:hover .settings-icon {
  transform: rotate(15deg) scale(1.1);
}

/* 语言下拉菜单样式 - 使用设计系统变量 */
:deep(.n-dropdown-menu) {
  background: rgba(255, 255, 255, 0.95) !important;
  backdrop-filter: blur(20px) saturate(180%);
  border: var(--border-width-thin) solid var(--border-color-base) !important;
  border-radius: var(--radius-lg) !important;
  box-shadow: var(--shadow-warm-lg) !important;
  padding: var(--spacing-xs) !important;
  margin-top: var(--spacing-sm) !important;
}

:deep(.n-dropdown-option) {
  padding: var(--spacing-sm) var(--spacing-md) !important;
  border-radius: var(--radius-md) !important;
  margin: var(--spacing-xs) 0 !important;
  transition: all var(--transition-fast) !important;
  color: var(--text-secondary) !important;
  font-weight: var(--font-weight-medium) !important;
}

:deep(.n-dropdown-option:hover) {
  background: linear-gradient(135deg, var(--color-primary-lighter) 0%, var(--color-secondary-lighter) 100%) !important;
  color: var(--color-primary-darker) !important;
  transform: translateX(2px);
}

:deep(.n-dropdown-option--selected) {
  background: linear-gradient(135deg, var(--color-primary-light) 0%, var(--color-secondary-light) 100%) !important;
  color: var(--color-primary-darker) !important;
  font-weight: var(--font-weight-semibold) !important;
}

.header-decoration {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: var(--border-width-thin);
  background: linear-gradient(
    90deg,
    transparent 0%,
    var(--border-color-light) 20%,
    var(--border-color-base) 50%,
    var(--border-color-light) 80%,
    transparent 100%
  );
  opacity: 0.6;
}

.content-wrapper {
  width: 100%;
  margin: 0;
  padding: var(--spacing-xl) var(--spacing-lg);
  min-height: calc(100vh - 100px);
  position: relative;
  z-index: var(--z-base);
  box-sizing: border-box;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .content-wrapper {
    padding: 1.5rem 1rem;
  }
  
  .header-container {
    padding: 0 1.5rem;
  }
}

@media (max-width: 768px) {
  .header-container {
    padding: 0 1rem;
  }
  
  .header-content {
    padding: 1rem 0;
    flex-wrap: wrap;
  }
  
  .logo-section {
    flex: 1;
    min-width: 200px;
  }
  
  .app-logo {
    width: 40px;
    height: 40px;
  }
  
  .app-title {
    font-size: 1.5rem;
  }
  
  .nav-section {
    gap: 0.75rem;
    width: 100%;
    margin-top: 0.75rem;
    justify-content: space-between;
  }
  
  .warm-menu :deep(.n-menu-item) {
    padding: 8px 12px;
    font-size: 0.85rem;
  }
  
  .content-wrapper {
    padding: 1rem 0.75rem;
  }
  
  .warm-header {
    backdrop-filter: blur(20px) saturate(180%);
  }
}

@media (max-width: 480px) {
  .app-title {
    font-size: 1.25rem;
  }
  
  .app-logo {
    width: 36px;
    height: 36px;
  }
  
  .warm-menu :deep(.n-menu-item) {
    padding: 6px 10px;
    font-size: 0.8rem;
  }
  
  .locale-button,
  .settings-button {
    width: 36px;
    height: 36px;
  }
  
  .locale-icon,
  .settings-icon {
    font-size: 18px;
  }
  
  .header-content {
    padding: 0.75rem 0;
  }
  
  .logo-section {
    gap: 0.75rem;
  }
}

:global(body.card-fullscreen-active) .warm-header {
  opacity: 0;
  transform: translateY(-100%);
  pointer-events: none;
}

:global(body.card-fullscreen-active) .content-wrapper {
  padding-top: var(--spacing-sm);
}
</style>

