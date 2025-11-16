<template>
  <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
    <!-- 左侧：时间轴 -->
    <div class="md:col-span-1">
      <n-card>
        <h2 class="text-lg font-semibold mb-4">{{ $t('journal.last30Days') }}</h2>
        <div class="space-y-2 max-h-[600px] overflow-y-auto">
          <div v-if="dailyList.length === 0" class="text-sm text-gray-500 text-center py-8">
            {{ $t('common.noData') }}
          </div>
          <div
            v-for="item in dailyList"
            :key="item.date"
            :class="[
              'w-full text-left p-3 rounded-lg transition-colors cursor-pointer',
              selectedDate === item.date
                ? 'bg-blue-50 border-2 border-blue-500'
                : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent',
            ]"
            @click="setSelectedDate(item.date)"
          >
            <div class="flex items-center space-x-3">
              <div
                :class="['w-4 h-4 rounded-full', getEmotionColor(item.main_emotion)]"
              />
              <div class="flex-1">
                <div class="text-sm font-medium text-gray-900">
                  {{ formatDate(item.date) }}
                </div>
                <div class="text-xs text-gray-500">
                  {{ getEmotionLabel(item.main_emotion) }}
                  <span v-if="item.avg_intensity">
                    · {{ $t('journal.avgIntensity') }} {{ item.avg_intensity.toFixed(1) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </n-card>
    </div>

    <!-- 右侧：详情 -->
    <div class="md:col-span-2">
      <n-card>
        <n-spin :show="loading">
          <div v-if="detail">
            <div class="mb-6">
              <h2 class="text-xl font-semibold mb-2">
                {{ formatDateFull(detail.date) }}
              </h2>
              <p v-if="detail.summary_text" class="text-gray-700 mb-4">
                {{ detail.summary_text }}
              </p>
              <div class="flex items-center space-x-4 text-sm">
                <span class="text-gray-600">
                  {{ $t('journal.mainEmotion') }}:
                  <span class="font-medium">{{ getEmotionLabel(detail.main_emotion) }}</span>
                </span>
                <span v-if="detail.avg_intensity" class="text-gray-600">
                  {{ $t('journal.avgIntensity') }}:
                  <span class="font-medium">{{ detail.avg_intensity.toFixed(1) }}</span>
                </span>
              </div>
              <div v-if="detail.main_topics && detail.main_topics.length > 0" class="mt-4">
                <span class="text-sm text-gray-600">{{ $t('journal.topics') }}: </span>
                <div class="flex flex-wrap gap-2 mt-2">
                  <n-tag
                    v-for="(topic, index) in detail.main_topics"
                    :key="index"
                    type="info"
                    size="small"
                  >
                    {{ topic }}
                  </n-tag>
                </div>
              </div>
            </div>

            <div v-if="detail.messages && detail.messages.length > 0">
              <h3 class="text-lg font-semibold mb-4">{{ $t('journal.representativeMessages') }}</h3>
              <div class="space-y-4">
                <div
                  v-for="msg in detail.messages"
                  :key="msg.id"
                  :class="[
                    'p-4 rounded-lg border-l-4',
                    msg.role === 'user'
                      ? 'bg-blue-50 border-blue-500'
                      : 'bg-gray-50 border-gray-300',
                  ]"
                >
                  <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-medium text-gray-700">
                      {{ msg.role === 'user' ? $t('journal.you') : $t('journal.assistant') }}
                    </span>
                    <span class="text-xs text-gray-500">
                      {{ formatTime(msg.created_at) }}
                    </span>
                  </div>
                  <p class="text-gray-900">{{ msg.content }}</p>
                  <div v-if="msg.emotion" class="mt-2 text-xs text-gray-500">
                    {{ getEmotionLabel(msg.emotion) }}
                    <span v-if="msg.intensity"> · {{ $t('journal.avgIntensity') }} {{ msg.intensity }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-12 text-gray-500">
            {{ $t('journal.selectDate') }}
          </div>
        </n-spin>
      </n-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { format, subDays, parseISO } from 'date-fns'
import { zhCN, enUS } from 'date-fns/locale'
import { NCard, NSpin, NTag } from 'naive-ui'
import {
  getDailyList,
  getDailyDetail,
  type DailySummaryItem,
  type DailyDetailResponse,
} from '@/lib/api'

const { t, locale } = useI18n()

const dailyList = ref<DailySummaryItem[]>([])
const selectedDate = ref<string | null>(null)
const detail = ref<DailyDetailResponse | null>(null)
const loading = ref(false)

const dateLocale = computed(() => {
  return locale.value === 'zh' ? zhCN : enUS
})

onMounted(() => {
  loadDailyList()
})

watch(selectedDate, (newDate) => {
  if (newDate) {
    loadDailyDetail(newDate)
  }
})

const loadDailyList = async () => {
  try {
    const toDate = format(new Date(), 'yyyy-MM-dd')
    const fromDate = format(subDays(new Date(), 30), 'yyyy-MM-dd')

    const response = await getDailyList(fromDate, toDate)
    if (response.error) {
      console.error('Error loading daily list:', response.error)
      return
    }

    if (response.data) {
      dailyList.value = response.data.items
      // 默认选择今天
      if (response.data.items.length > 0) {
        selectedDate.value = response.data.items[0].date
      }
    }
  } catch (error) {
    console.error('Failed to load daily list:', error)
  }
}

const loadDailyDetail = async (date: string) => {
  loading.value = true
  try {
    const response = await getDailyDetail(date)
    if (response.error) {
      console.error('Error loading daily detail:', response.error)
      return
    }

    if (response.data) {
      detail.value = response.data
    }
  } catch (error) {
    console.error('Failed to load daily detail:', error)
  } finally {
    loading.value = false
  }
}

const setSelectedDate = (date: string) => {
  selectedDate.value = date
}

const getEmotionColor = (emotion: string | null) => {
  if (!emotion) return 'bg-gray-200'
  const colors: Record<string, string> = {
    joy: 'bg-yellow-400',
    sadness: 'bg-blue-400',
    anxiety: 'bg-orange-400',
    anger: 'bg-red-400',
    tired: 'bg-purple-400',
    neutral: 'bg-gray-300',
    relief: 'bg-green-400',
    calm: 'bg-teal-400',
  }
  return colors[emotion] || 'bg-gray-200'
}

const getEmotionLabel = (emotion: string | null) => {
  if (!emotion) return t('emotions.none')
  const emotionKey = emotion as keyof typeof import('@/i18n/zh').default.emotions
  try {
    return t(`emotions.${emotionKey}`) || emotion
  } catch {
    return emotion
  }
}

const formatDate = (dateStr: string) => {
  return format(parseISO(dateStr), 'M月d日', { locale: dateLocale.value })
}

const formatDateFull = (dateStr: string) => {
  return format(parseISO(dateStr), 'yyyy年M月d日', { locale: dateLocale.value })
}

const formatTime = (dateStr: string) => {
  return format(parseISO(dateStr), 'HH:mm', { locale: dateLocale.value })
}
</script>

<style scoped>
.grid {
  display: grid;
}

.gap-6 {
  gap: 1.5rem;
}

.grid-cols-1 {
  grid-template-columns: repeat(1, minmax(0, 1fr));
}

@media (min-width: 768px) {
  .md\:grid-cols-3 {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
  .md\:col-span-1 {
    grid-column: span 1 / span 1;
  }
  .md\:col-span-2 {
    grid-column: span 2 / span 2;
  }
}

.space-y-2 > * + * {
  margin-top: 0.5rem;
}

.space-y-4 > * + * {
  margin-top: 1rem;
}

.space-x-3 > * + * {
  margin-left: 0.75rem;
}

.space-x-4 > * + * {
  margin-left: 1rem;
}
</style>

