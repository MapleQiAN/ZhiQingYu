<template>
  <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
    <!-- 左侧：时间轴 -->
    <div class="md:col-span-1">
      <n-card class="timeline-card">
        <div class="card-header">
          <h2 class="card-title">{{ $t('journal.last30Days') }}</h2>
        </div>
        <div class="timeline-container">
          <div v-if="dailyList.length === 0" class="empty-timeline">
            <div class="empty-icon">📅</div>
            <p class="empty-text">{{ $t('common.noData') }}</p>
          </div>
          <div
            v-for="item in dailyList"
            :key="item.date"
            :class="[
              'timeline-item',
              selectedDate === item.date ? 'timeline-item-active' : '',
            ]"
            @click="setSelectedDate(item.date)"
          >
            <div class="timeline-dot-wrapper">
              <div
                class="timeline-dot"
                :style="{ backgroundColor: getEmotionColorHex(item.main_emotion) }"
              />
            </div>
            <div class="timeline-content">
              <div class="timeline-date">
                {{ formatDate(item.date) }}
              </div>
              <div class="timeline-emotion">
                <span class="emotion-label">{{ getEmotionLabel(item.main_emotion) }}</span>
                <span v-if="item.avg_intensity" class="intensity-badge">
                  {{ item.avg_intensity.toFixed(1) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </n-card>
    </div>

    <!-- 右侧：详情 -->
    <div class="md:col-span-2">
      <n-card class="detail-card">
        <n-spin :show="loading">
          <div v-if="detail" class="detail-content">
            <div class="detail-header">
              <h2 class="detail-title">
                {{ formatDateFull(detail.date) }}
              </h2>
              <div class="detail-meta">
                <div class="meta-item">
                  <span class="meta-label">{{ $t('journal.mainEmotion') }}</span>
                  <span class="meta-value emotion-highlight">
                    {{ getEmotionLabel(detail.main_emotion) }}
                  </span>
                </div>
                <div v-if="detail.avg_intensity" class="meta-item">
                  <span class="meta-label">{{ $t('journal.avgIntensity') }}</span>
                  <span class="meta-value">{{ detail.avg_intensity.toFixed(1) }}</span>
                </div>
              </div>
              <p v-if="detail.summary_text" class="summary-text">
                {{ detail.summary_text }}
              </p>
              <div v-if="detail.main_topics && detail.main_topics.length > 0" class="topics-section">
                <span class="topics-label">{{ $t('journal.topics') }}</span>
                <div class="topics-list">
                  <n-tag
                    v-for="(topic, index) in detail.main_topics"
                    :key="index"
                    class="topic-tag"
                    size="medium"
                  >
                    {{ topic }}
                  </n-tag>
                </div>
              </div>
            </div>

            <div v-if="detail.messages && detail.messages.length > 0" class="messages-section">
              <h3 class="section-title">{{ $t('journal.representativeMessages') }}</h3>
              <div class="messages-list">
                <div
                  v-for="msg in detail.messages"
                  :key="msg.id"
                  :class="[
                    'message-card',
                    msg.role === 'user' ? 'message-user' : 'message-assistant',
                  ]"
                >
                  <div class="message-header">
                    <span class="message-role">
                      {{ msg.role === 'user' ? $t('journal.you') : $t('journal.assistant') }}
                    </span>
                    <span class="message-time">
                      {{ formatTime(msg.created_at) }}
                    </span>
                  </div>
                  <p class="message-body">{{ msg.content }}</p>
                  <div v-if="msg.emotion" class="message-emotion">
                    <span class="emotion-indicator">{{ getEmotionLabel(msg.emotion) }}</span>
                    <span v-if="msg.intensity" class="intensity-indicator">
                      {{ msg.intensity }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="empty-detail">
            <div class="empty-icon-large">📔</div>
            <p class="empty-text-large">{{ $t('journal.selectDate') }}</p>
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

const getEmotionColorHex = (emotion: string | null) => {
  if (!emotion) return '#E0E0E0'
  const colors: Record<string, string> = {
    joy: '#FFD4A3',
    sadness: '#B3D9FF',
    anxiety: '#FFB3BA',
    anger: '#FF9F9F',
    tired: '#D4B3FF',
    neutral: '#E0E0E0',
    relief: '#B3FFB3',
    calm: '#B3E5D1',
  }
  return colors[emotion] || '#E0E0E0'
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

.timeline-card {
  background: rgba(255, 255, 255, 0.98) !important;
  border: 1px solid rgba(255, 182, 193, 0.25) !important;
  border-radius: 24px !important;
  box-shadow: 0 4px 24px rgba(255, 182, 193, 0.12) !important;
  backdrop-filter: blur(20px);
  transition: all 0.3s ease;
  outline: none !important;
}

.timeline-card :deep(.n-card) {
  outline: none !important;
  border: none !important;
}

.timeline-card :deep(.n-card__content) {
  outline: none !important;
}

.timeline-card:hover {
  box-shadow: 0 6px 32px rgba(255, 182, 193, 0.18) !important;
}

.card-header {
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(255, 182, 193, 0.15);
}

.card-title {
  font-size: 1.25rem;
  font-weight: 600;
  background: linear-gradient(135deg, #D9779F 0%, #C97A9A 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
}

.timeline-container {
  max-height: 600px;
  overflow-y: auto;
  padding-right: 4px;
}

.timeline-container::-webkit-scrollbar {
  width: 6px;
}

.timeline-container::-webkit-scrollbar-track {
  background: rgba(255, 182, 193, 0.05);
  border-radius: 10px;
}

.timeline-container::-webkit-scrollbar-thumb {
  background: rgba(255, 182, 193, 0.3);
  border-radius: 10px;
}

.empty-timeline {
  text-align: center;
  padding: 3rem 1rem;
  color: #B8A8A8;
}

.empty-icon {
  font-size: 3rem;
  opacity: 0.5;
  margin-bottom: 1rem;
}

.empty-text {
  font-size: 0.9rem;
}

.timeline-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1.25rem;
  margin-bottom: 0.75rem;
  border-radius: 18px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: rgba(255, 250, 245, 0.6);
  border: 2px solid transparent;
  position: relative;
}

.timeline-item:hover {
  background: rgba(255, 245, 245, 0.8);
  transform: translateX(6px);
  border-color: rgba(255, 182, 193, 0.35);
  box-shadow: 0 4px 16px rgba(255, 182, 193, 0.15);
}

.timeline-item-active {
  background: linear-gradient(135deg, rgba(255, 182, 193, 0.2) 0%, rgba(255, 218, 185, 0.2) 100%);
  border-color: rgba(255, 182, 193, 0.45);
  box-shadow: 0 6px 20px rgba(255, 182, 193, 0.25);
  transform: translateX(4px);
}

.timeline-dot-wrapper {
  flex-shrink: 0;
  padding-top: 2px;
}

.timeline-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  border: 2px solid white;
}

.timeline-content {
  flex: 1;
  min-width: 0;
}

.timeline-date {
  font-size: 0.95rem;
  font-weight: 600;
  color: #8B6F7E;
  margin-bottom: 0.25rem;
}

.timeline-emotion {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.emotion-label {
  font-size: 0.85rem;
  color: #A68A8A;
}

.intensity-badge {
  font-size: 0.75rem;
  padding: 2px 8px;
  background: rgba(255, 182, 193, 0.2);
  border-radius: 10px;
  color: #8B6F7E;
  font-weight: 500;
}

.detail-card {
  background: rgba(255, 255, 255, 0.98) !important;
  border: 1px solid rgba(255, 182, 193, 0.25) !important;
  border-radius: 24px !important;
  box-shadow: 0 4px 24px rgba(255, 182, 193, 0.12) !important;
  backdrop-filter: blur(20px);
  min-height: 600px;
  transition: all 0.3s ease;
  outline: none !important;
}

.detail-card :deep(.n-card) {
  outline: none !important;
  border: none !important;
}

.detail-card :deep(.n-card__content) {
  outline: none !important;
}

.detail-card:hover {
  box-shadow: 0 6px 32px rgba(255, 182, 193, 0.18) !important;
}

.detail-content {
  animation: fadeIn 0.4s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.detail-header {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid rgba(255, 182, 193, 0.15);
}

.detail-title {
  font-size: 1.75rem;
  font-weight: 700;
  background: linear-gradient(135deg, #D9779F 0%, #C97A9A 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 1rem 0;
}

.detail-meta {
  display: flex;
  gap: 2rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.meta-label {
  font-size: 0.9rem;
  color: #A68A8A;
}

.meta-value {
  font-size: 0.95rem;
  font-weight: 600;
  color: #8B6F7E;
}

.emotion-highlight {
  padding: 4px 12px;
  background: linear-gradient(135deg, rgba(255, 182, 193, 0.15) 0%, rgba(255, 218, 185, 0.15) 100%);
  border-radius: 12px;
  border: 1px solid rgba(255, 182, 193, 0.3);
}

.summary-text {
  font-size: 1rem;
  line-height: 1.7;
  color: #6B5A6B;
  margin: 1rem 0;
  padding: 1rem;
  background: rgba(255, 250, 245, 0.6);
  border-radius: 12px;
  border-left: 3px solid rgba(255, 182, 193, 0.4);
}

.topics-section {
  margin-top: 1.5rem;
}

.topics-label {
  display: block;
  font-size: 0.9rem;
  color: #A68A8A;
  margin-bottom: 0.75rem;
  font-weight: 500;
}

.topics-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.topic-tag {
  background: linear-gradient(135deg, rgba(255, 182, 193, 0.2) 0%, rgba(255, 218, 185, 0.2) 100%) !important;
  border: 1px solid rgba(255, 182, 193, 0.35) !important;
  color: #8B6F7E !important;
  border-radius: 18px !important;
  padding: 8px 16px !important;
  font-weight: 500 !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 6px rgba(255, 182, 193, 0.1);
}

.topic-tag:hover {
  transform: translateY(-3px) scale(1.05);
  box-shadow: 0 4px 12px rgba(255, 182, 193, 0.25);
  border-color: rgba(255, 182, 193, 0.5) !important;
}

.messages-section {
  margin-top: 2rem;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #8B6F7E;
  margin-bottom: 1.5rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid rgba(255, 182, 193, 0.15);
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.message-card {
  padding: 1.5rem;
  border-radius: 18px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-left: 4px solid;
  animation: slideIn 0.4s ease;
  box-shadow: 0 2px 8px rgba(255, 182, 193, 0.08);
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.message-user {
  background: linear-gradient(135deg, rgba(255, 182, 193, 0.1) 0%, rgba(255, 218, 185, 0.1) 100%);
  border-left-color: #FFB6C1;
}

.message-assistant {
  background: rgba(255, 250, 245, 0.6);
  border-left-color: rgba(255, 182, 193, 0.3);
}

.message-card:hover {
  transform: translateX(6px);
  box-shadow: 0 6px 20px rgba(255, 182, 193, 0.2);
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.message-role {
  font-size: 0.9rem;
  font-weight: 600;
  color: #8B6F7E;
}

.message-time {
  font-size: 0.8rem;
  color: #B8A8A8;
}

.message-body {
  font-size: 0.95rem;
  line-height: 1.7;
  color: #4A4A4A;
  margin: 0;
}

.message-emotion {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid rgba(255, 182, 193, 0.1);
}

.emotion-indicator {
  font-size: 0.8rem;
  padding: 3px 10px;
  background: rgba(255, 182, 193, 0.15);
  border-radius: 10px;
  color: #8B6F7E;
  font-weight: 500;
}

.intensity-indicator {
  font-size: 0.75rem;
  color: #B8A8A8;
}

.empty-detail {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 5rem 1rem;
  color: #B8A8A8;
  min-height: 400px;
}

.empty-icon-large {
  font-size: 5rem;
  opacity: 0.5;
  margin-bottom: 1.5rem;
  filter: drop-shadow(0 4px 8px rgba(255, 182, 193, 0.2));
}

.empty-text-large {
  font-size: 1.1rem;
}
</style>

