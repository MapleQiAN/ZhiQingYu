<template>
  <div class="min-h-screen warm-bg">
    <n-layout>
      <n-layout-header bordered class="warm-header">
        <div class="header-container">
          <div class="header-content">
            <div class="logo-section group cursor-pointer" @click="router.push('/')">
              <div class="app-logo-wrapper">
                <div class="app-logo">🌺</div>
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
.warm-bg {
  background: linear-gradient(135deg, #FFF9F5 0%, #FFF5ED 50%, #FFF0E6 100%);
  min-height: 100vh;
  position: relative;
}

.warm-bg::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 50%, rgba(255, 182, 193, 0.08) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(255, 218, 185, 0.08) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
}

.warm-header {
  background: rgba(255, 255, 255, 0.9) !important;
  backdrop-filter: blur(25px) saturate(180%);
  -webkit-backdrop-filter: blur(25px) saturate(180%);
  box-shadow: 
    0 4px 30px rgba(255, 182, 193, 0.12),
    0 1px 0 rgba(255, 255, 255, 0.8) inset;
  border-bottom: 1px solid rgba(255, 182, 193, 0.2) !important;
  position: sticky;
  top: 0;
  z-index: 100;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.warm-header:hover {
  box-shadow: 
    0 8px 45px rgba(255, 182, 193, 0.18),
    0 1px 0 rgba(255, 255, 255, 0.9) inset;
  border-bottom-color: rgba(255, 182, 193, 0.3) !important;
}

.header-container {
  position: relative;
  width: 100%;
  margin: 0;
  padding: 0 2rem;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 0;
  position: relative;
  z-index: 2;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: transform 0.3s ease;
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
  font-size: 36px;
  line-height: 1;
  filter: drop-shadow(0 3px 6px rgba(255, 182, 193, 0.4));
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
  z-index: 2;
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
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 182, 193, 0.4) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.3s ease;
  z-index: 1;
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
  font-size: 1.75rem;
  font-weight: 700;
  background: linear-gradient(135deg, #D9779F 0%, #C97A9A 50%, #E8A5C4 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 0.8px;
  margin: 0;
  line-height: 1.2;
  transition: all 0.3s ease;
  position: relative;
}

.logo-section:hover .app-title {
  background: linear-gradient(135deg, #E8A5C4 0%, #D9779F 50%, #C97A9A 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  transform: translateX(2px);
}

.title-underline {
  height: 3px;
  width: 0;
  background: linear-gradient(90deg, #FFB6C1 0%, #FFA07A 100%);
  border-radius: 2px;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  margin-top: 2px;
}

.logo-section:hover .title-underline {
  width: 100%;
}

.nav-section {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.divider {
  width: 1px;
  height: 24px;
  background: linear-gradient(180deg, transparent 0%, rgba(255, 182, 193, 0.3) 50%, transparent 100%);
}

.warm-menu {
  background: transparent !important;
}

.warm-menu :deep(.n-menu) {
  background: transparent !important;
}

.warm-menu :deep(.n-menu-item) {
  color: #8B6F7E;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-weight: 500;
  padding: 10px 20px;
  border-radius: 14px;
  margin: 0 2px;
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
  color: #D9779F !important;
  background: linear-gradient(135deg, rgba(255, 182, 193, 0.2) 0%, rgba(255, 218, 185, 0.2) 100%) !important;
  font-weight: 600;
  box-shadow: 
    0 4px 12px rgba(255, 182, 193, 0.25),
    0 0 0 1px rgba(255, 182, 193, 0.1) inset;
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
  background: linear-gradient(90deg, #FFB6C1 0%, #FFA07A 100%);
  border-radius: 2px;
}

.warm-menu :deep(.n-menu-item:hover) {
  color: #D9779F;
  background: linear-gradient(135deg, rgba(255, 182, 193, 0.12) 0%, rgba(255, 218, 185, 0.12) 100%);
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(255, 182, 193, 0.15);
}

.locale-button,
.settings-button {
  width: 40px;
  height: 40px;
  border-radius: 50% !important;
  background: rgba(255, 255, 255, 0.6) !important;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 182, 193, 0.3) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 6px rgba(255, 182, 193, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.locale-button:hover,
.settings-button:hover {
  background: rgba(255, 255, 255, 0.8) !important;
  border-color: rgba(255, 182, 193, 0.5) !important;
  box-shadow: 0 4px 12px rgba(255, 182, 193, 0.2);
  transform: translateY(-2px) scale(1.05);
}

.locale-icon,
.settings-icon {
  font-size: 20px;
  line-height: 1;
  filter: drop-shadow(0 2px 4px rgba(255, 182, 193, 0.3));
  transition: transform 0.3s ease;
}

.locale-button:hover .locale-icon,
.settings-button:hover .settings-icon {
  transform: rotate(15deg) scale(1.1);
}

/* 语言下拉菜单样式 */
:deep(.n-dropdown-menu) {
  background: rgba(255, 255, 255, 0.95) !important;
  backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255, 182, 193, 0.3) !important;
  border-radius: 12px !important;
  box-shadow: 
    0 8px 24px rgba(255, 182, 193, 0.2),
    0 2px 8px rgba(255, 182, 193, 0.1) !important;
  padding: 4px !important;
  margin-top: 8px !important;
}

:deep(.n-dropdown-option) {
  padding: 10px 16px !important;
  border-radius: 8px !important;
  margin: 2px 0 !important;
  transition: all 0.2s ease !important;
  color: #8B6F7E !important;
  font-weight: 500 !important;
}

:deep(.n-dropdown-option:hover) {
  background: linear-gradient(135deg, rgba(255, 182, 193, 0.15) 0%, rgba(255, 218, 185, 0.15) 100%) !important;
  color: #D9779F !important;
  transform: translateX(2px);
}

:deep(.n-dropdown-option--selected) {
  background: linear-gradient(135deg, rgba(255, 182, 193, 0.25) 0%, rgba(255, 218, 185, 0.25) 100%) !important;
  color: #D9779F !important;
  font-weight: 600 !important;
}

.header-decoration {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 182, 193, 0.3) 20%,
    rgba(255, 182, 193, 0.5) 50%,
    rgba(255, 182, 193, 0.3) 80%,
    transparent 100%
  );
  opacity: 0.6;
}

.content-wrapper {
  width: 100%;
  margin: 0;
  padding: 2rem 1.5rem;
  min-height: calc(100vh - 100px);
  position: relative;
  z-index: 1;
  box-sizing: border-box;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .content-wrapper {
    padding: 1.5rem 1rem;
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
    font-size: 28px;
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
}

@media (max-width: 480px) {
  .app-title {
    font-size: 1.25rem;
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
}
</style>

