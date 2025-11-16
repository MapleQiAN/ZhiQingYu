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
              <n-select
                v-model:value="currentLocale"
                :options="localeOptions"
                size="small"
                class="locale-select"
                @update:value="handleLocaleChange"
              />
            </div>
          </div>
          <div class="header-decoration"></div>
        </div>
      </n-layout-header>
      <n-layout-content>
        <div class="max-w-7xl mx-auto px-6 py-10">
          <slot />
        </div>
      </n-layout-content>
    </n-layout>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  NLayout,
  NLayoutHeader,
  NLayoutContent,
  NMenu,
  NSelect,
} from 'naive-ui'
import type { MenuOption } from 'naive-ui'

const router = useRouter()
const route = useRoute()
const { locale, t } = useI18n()

const currentLocale = ref(locale.value)

const localeOptions = [
  { label: '中文', value: 'zh' },
  { label: 'English', value: 'en' },
]

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

const activeKey = computed(() => route.path)

const handleMenuSelect = (key: string) => {
  router.push(key)
}

const handleLocaleChange = (value: string) => {
  locale.value = value
  localStorage.setItem('locale', value)
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
  max-width: 1400px;
  margin: 0 auto;
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

.locale-select {
  min-width: 100px;
}

.locale-select :deep(.n-base-selection) {
  border-color: rgba(255, 182, 193, 0.3) !important;
  border-radius: 12px !important;
  background: rgba(255, 255, 255, 0.6) !important;
  backdrop-filter: blur(10px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 6px rgba(255, 182, 193, 0.1);
}

.locale-select :deep(.n-base-selection:hover) {
  border-color: rgba(255, 182, 193, 0.5) !important;
  box-shadow: 0 4px 12px rgba(255, 182, 193, 0.2);
  background: rgba(255, 255, 255, 0.8) !important;
  transform: translateY(-1px);
}

.locale-select :deep(.n-base-selection--active) {
  border-color: rgba(255, 182, 193, 0.6) !important;
  box-shadow: 0 4px 16px rgba(255, 182, 193, 0.25);
}

.locale-select :deep(.n-base-selection-label) {
  color: #8B6F7E;
  font-weight: 500;
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

/* 响应式设计 */
@media (max-width: 768px) {
  .header-container {
    padding: 0 1rem;
  }
  
  .header-content {
    padding: 1rem 0;
  }
  
  .app-logo {
    font-size: 28px;
  }
  
  .app-title {
    font-size: 1.5rem;
  }
  
  .nav-section {
    gap: 1rem;
  }
  
  .warm-menu :deep(.n-menu-item) {
    padding: 8px 12px;
    font-size: 0.9rem;
  }
}
</style>

