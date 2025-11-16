<template>
  <div class="min-h-screen bg-gray-50">
    <n-layout>
      <n-layout-header bordered class="bg-white">
        <div class="max-w-4xl mx-auto px-4 py-3">
          <div class="flex items-center justify-between">
            <h1 class="text-xl font-semibold text-gray-900">
              {{ $t('common.appName') }}
            </h1>
            <div class="flex items-center space-x-6">
              <n-menu
                mode="horizontal"
                :value="activeKey"
                :options="menuOptions"
                @update:value="handleMenuSelect"
              />
              <n-select
                v-model:value="currentLocale"
                :options="localeOptions"
                size="small"
                style="width: 100px"
                @update:value="handleLocaleChange"
              />
            </div>
          </div>
        </div>
      </n-layout-header>
      <n-layout-content>
        <div class="max-w-4xl mx-auto px-4 py-8">
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
.bg-gray-50 {
  background-color: #f5f5f5;
}
</style>

