<template>
  <div class="overview-container">
    <!-- 顶部标题区域 -->
    <div class="header-section">
      <div class="title-group">
        <h1 class="main-title">{{ $t('common.appName') }}</h1>
        <p class="subtitle">{{ $t('overview.subtitle') }}</p>
      </div>
      <div class="action-buttons">
        <n-button
          type="primary"
          class="warm-button"
          @click="loadStats"
          :loading="loading"
        >
          <template #icon>
            <n-icon><RefreshIcon /></n-icon>
          </template>
          {{ $t('overview.refreshData') }}
        </n-button>
        <div class="time-selector">
          <span class="time-label">{{ $t('overview.statsDays') }}:</span>
          <n-button-group>
            <n-button
              v-for="d in [7, 14, 30]"
              :key="d"
              :type="days === d ? 'primary' : 'default'"
              size="small"
              class="warm-button-small"
              @click="setDays(d)"
            >
              {{ d }}{{ $t('common.days') }}
            </n-button>
          </n-button-group>
        </div>
      </div>
    </div>

    <n-spin :show="loading">
      <div v-if="stats">
        <!-- 关键指标卡片 -->
        <div class="stats-cards">
          <n-card class="warm-card stat-card" hoverable>
            <div class="stat-content">
              <div class="stat-icon stat-icon-1">📅</div>
              <div class="stat-info">
                <div class="stat-value">{{ days }}</div>
                <div class="stat-label">{{ $t('overview.totalDays') }}</div>
                <div class="stat-desc">{{ $t('overview.totalDaysDesc') }}</div>
              </div>
            </div>
          </n-card>

          <n-card class="warm-card stat-card" hoverable>
            <div class="stat-content">
              <div class="stat-icon stat-icon-2">💭</div>
              <div class="stat-info">
                <div class="stat-value">{{ emotionRecordsCount }}</div>
                <div class="stat-label">{{ $t('overview.emotionRecords') }}</div>
                <div class="stat-desc">{{ $t('overview.emotionRecordsDesc') }}</div>
              </div>
            </div>
          </n-card>

          <n-card class="warm-card stat-card" hoverable>
            <div class="stat-content">
              <div class="stat-icon stat-icon-3">🎭</div>
              <div class="stat-info">
                <div class="stat-value">{{ emotionTypesCount }}</div>
                <div class="stat-label">{{ $t('overview.emotionTypes') }}</div>
                <div class="stat-desc">{{ $t('overview.emotionTypesDesc') }}</div>
              </div>
            </div>
          </n-card>

          <n-card class="warm-card stat-card" hoverable>
            <div class="stat-content">
              <div class="stat-icon stat-icon-4">📈</div>
              <div class="stat-info">
                <div class="stat-value">{{ trendPercentage }}</div>
                <div class="stat-label">{{ $t('overview.emotionScore') }}</div>
                <div class="stat-desc">
                  {{ $t('overview.trendGrowth') }}
                  <span class="trend-up">↑</span>
                </div>
              </div>
            </div>
          </n-card>
        </div>

        <!-- 主要内容区域 -->
        <div class="main-content">
          <!-- 左侧面板 -->
          <div class="left-panel">
            <!-- 情绪类型分布 -->
            <n-card class="warm-card panel-card" :title="$t('overview.emotionTypeDistribution')">
              <template #header-extra>
                <n-icon class="panel-icon">📊</n-icon>
              </template>
              <div v-if="emotionData.length === 0" class="empty-state">
                <div class="empty-icon">📊</div>
                <p>{{ $t('overview.noData') }}</p>
              </div>
              <div v-else style="width: 100%; height: 250px">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart :data="emotionData">
                    <CartesianGrid stroke-dasharray="3 3" stroke="#FFE5E5" />
                    <XAxis :data-key="'emotion'" />
                    <YAxis />
                    <Tooltip />
                    <Bar
                      data-key="value"
                      :name="$t('overview.percentage')"
                      fill="#FFB6C1"
                      :radius="[8, 8, 0, 0]"
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </n-card>

            <!-- 最近的情绪记录 -->
            <n-card class="warm-card panel-card" :title="$t('overview.recentEmotions')">
              <template #header-extra>
                <n-icon class="panel-icon">🕐</n-icon>
              </template>
              <div v-if="recentEmotions.length === 0" class="empty-state">
                <div class="empty-icon">📝</div>
                <p>{{ $t('overview.noData') }}</p>
              </div>
              <div v-else class="recent-list">
                <div
                  v-for="(item, index) in recentEmotions"
                  :key="index"
                  class="recent-item"
                >
                  <div class="recent-date">{{ formatDate(item.date) }}</div>
                  <div class="recent-emotion">
                    <span
                      class="emotion-badge"
                      :style="{ backgroundColor: getEmotionColor(item.main_emotion) }"
                    >
                      {{ getEmotionLabel(item.main_emotion) }}
                    </span>
                    <span v-if="item.avg_intensity" class="intensity-text">
                      {{ item.avg_intensity.toFixed(1) }}
                    </span>
                  </div>
                </div>
              </div>
            </n-card>
          </div>

          <!-- 中间面板 -->
          <div class="middle-panel">
            <n-card class="warm-card panel-card" :title="$t('overview.coreEmotionRanking')">
              <template #header-extra>
                <n-icon class="panel-icon">🏆</n-icon>
              </template>
              <div v-if="stats.top_topics.length === 0" class="empty-state">
                <div class="empty-icon">📊</div>
                <p>{{ $t('overview.noEmotionData') }}</p>
              </div>
              <div v-else class="topics-list">
                <div
                  v-for="(item, index) in stats.top_topics"
                  :key="index"
                  class="topic-item"
                >
                  <div class="topic-rank">{{ index + 1 }}</div>
                  <div class="topic-info">
                    <div class="topic-name">{{ item.topic }}</div>
                    <div class="topic-count">{{ item.count }} {{ $t('overview.emotionRecords') }}</div>
                  </div>
                </div>
              </div>
            </n-card>
          </div>

          <!-- 右侧面板 -->
          <div class="right-panel">
            <n-card class="warm-card panel-card" :title="$t('overview.quickActions')">
              <template #header-extra>
                <n-icon class="panel-icon">🚀</n-icon>
              </template>
              <div class="quick-actions">
                <div class="action-item" @click="goToChat">
                  <div class="action-icon action-icon-1">💬</div>
                  <div class="action-content">
                    <div class="action-title">{{ $t('overview.startChat') }}</div>
                    <div class="action-desc">{{ $t('overview.startChatDesc') }}</div>
                  </div>
                  <div class="action-arrow">→</div>
                </div>

                <div class="action-item" @click="goToJournal">
                  <div class="action-icon action-icon-2">📔</div>
                  <div class="action-content">
                    <div class="action-title">{{ $t('overview.viewJournal') }}</div>
                    <div class="action-desc">{{ $t('overview.viewJournalDesc') }}</div>
                  </div>
                  <div class="action-arrow">→</div>
                </div>

                <div class="action-item" @click="goToStats">
                  <div class="action-icon action-icon-3">📊</div>
                  <div class="action-content">
                    <div class="action-title">{{ $t('overview.viewStats') }}</div>
                    <div class="action-desc">{{ $t('overview.viewStatsDesc') }}</div>
                  </div>
                  <div class="action-arrow">→</div>
                </div>
              </div>
            </n-card>
          </div>
        </div>
      </div>
      <div v-else class="empty-container">
        <div class="empty-state-large">
          <div class="empty-icon-large">📊</div>
          <p>{{ $t('overview.noData') }}</p>
        </div>
      </div>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { format, parseISO } from 'date-fns'
import {
  NCard,
  NButton,
  NButtonGroup,
  NSpin,
  NIcon,
} from 'naive-ui'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { RefreshOutline as RefreshIcon } from '@vicons/ionicons5'
import { getStatsOverview, getDailyList, type EmotionStatsOverview, type DailySummaryItem } from '@/lib/api'

const { t } = useI18n()
const router = useRouter()

const stats = ref<EmotionStatsOverview | null>(null)
const recentEmotions = ref<DailySummaryItem[]>([])
const loading = ref(true)
const days = ref(7)

onMounted(() => {
  loadStats()
  loadRecentEmotions()
})

watch(days, () => {
  loadStats()
})

const loadStats = async () => {
  loading.value = true
  try {
    const response = await getStatsOverview(days.value)
    if (response.error) {
      console.error('Error loading stats:', response.error)
      return
    }

    if (response.data) {
      stats.value = response.data
    }
  } catch (error) {
    console.error('Failed to load stats:', error)
  } finally {
    loading.value = false
  }
}

const loadRecentEmotions = async () => {
  try {
    const toDate = format(new Date(), 'yyyy-MM-dd')
    const fromDate = format(new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), 'yyyy-MM-dd')
    const response = await getDailyList(fromDate, toDate)
    if (response.data) {
      recentEmotions.value = response.data.items.slice(0, 5).reverse()
    }
  } catch (error) {
    console.error('Failed to load recent emotions:', error)
  }
}

const setDays = (d: number) => {
  days.value = d
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

const getEmotionColor = (emotion: string | null) => {
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

const formatDate = (dateStr: string) => {
  try {
    return format(parseISO(dateStr), 'M月d日')
  } catch {
    return dateStr
  }
}

// 计算统计数据
const emotionRecordsCount = computed(() => {
  if (!stats.value) return 0
  return stats.value.trend.length
})

const emotionTypesCount = computed(() => {
  if (!stats.value) return 0
  return Object.keys(stats.value.emotion_distribution).length
})

const trendPercentage = computed(() => {
  if (!stats.value || stats.value.trend.length === 0) return '0.0'
  const scores = stats.value.trend.map((t) => t.score)
  const avg = scores.reduce((a, b) => a + b, 0) / scores.length
  return avg.toFixed(1)
})

// 格式化情绪分布数据
const emotionData = computed(() => {
  if (!stats.value) return []
  return Object.entries(stats.value.emotion_distribution)
    .map(([emotion, value]) => ({
      emotion: getEmotionLabel(emotion),
      value: Number((value * 100).toFixed(1)),
    }))
    .sort((a, b) => b.value - a.value)
})

// 导航函数
const goToChat = () => {
  router.push('/')
}

const goToJournal = () => {
  router.push('/journal')
}

const goToStats = () => {
  // 已经在概览页面
}
</script>

<style scoped>
.overview-container {
  min-height: calc(100vh - 200px);
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1.5rem;
}

.title-group {
  flex: 1;
  min-width: 300px;
}

.main-title {
  font-size: 2.75rem;
  font-weight: 700;
  background: linear-gradient(135deg, #D9779F 0%, #C97A9A 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 0.5rem 0;
  letter-spacing: 0.5px;
  line-height: 1.2;
}

.subtitle {
  font-size: 1.05rem;
  color: #A68A8A;
  margin: 0;
  font-weight: 400;
  letter-spacing: 0.3px;
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.time-selector {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.time-label {
  color: #8B5A6B;
  font-size: 0.9rem;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.warm-card {
  background: rgba(255, 255, 255, 0.95) !important;
  border: 1px solid rgba(255, 182, 193, 0.2) !important;
  border-radius: 20px !important;
  box-shadow: 0 4px 20px rgba(255, 182, 193, 0.1) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  backdrop-filter: blur(10px);
}

.warm-card:hover {
  box-shadow: 0 8px 35px rgba(255, 182, 193, 0.2) !important;
  transform: translateY(-3px);
  border-color: rgba(255, 182, 193, 0.35) !important;
}

.stat-card {
  padding: 1.5rem !important;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.stat-icon {
  font-size: 3rem;
  width: 70px;
  height: 70px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  background: linear-gradient(135deg, #FFE5E5 0%, #FFD4D4 100%);
}

.stat-icon-1 {
  background: linear-gradient(135deg, #FFE5E5 0%, #FFD4D4 100%);
}

.stat-icon-2 {
  background: linear-gradient(135deg, #E5F3FF 0%, #D4E9FF 100%);
}

.stat-icon-3 {
  background: linear-gradient(135deg, #FFF5E5 0%, #FFE9D4 100%);
}

.stat-icon-4 {
  background: linear-gradient(135deg, #F0E5FF 0%, #E9D4FF 100%);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 2.75rem;
  font-weight: 700;
  background: linear-gradient(135deg, #D9779F 0%, #C97A9A 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
  margin-bottom: 0.5rem;
}

.stat-label {
  font-size: 1rem;
  font-weight: 600;
  color: #A68A8A;
  margin-bottom: 0.25rem;
}

.stat-desc {
  font-size: 0.85rem;
  color: #B8A8A8;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.trend-up {
  color: #4CAF50;
  font-weight: bold;
}

.main-content {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 1.5rem;
  margin-top: 1.5rem;
}

@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr 1fr;
  }
  .right-panel {
    grid-column: 1 / -1;
  }
}

@media (max-width: 768px) {
  .main-content {
    grid-template-columns: 1fr;
  }
  .stats-cards {
    grid-template-columns: 1fr;
  }
}

.panel-card {
  min-height: 400px;
}

.panel-icon {
  font-size: 1.2rem;
  margin-left: 0.5rem;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  color: #B8A8A8;
  min-height: 200px;
}

.empty-icon {
  font-size: 3rem;
  opacity: 0.5;
  margin-bottom: 1rem;
}

.empty-state-large {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 5rem 1rem;
  color: #B8A8A8;
}

.empty-icon-large {
  font-size: 5rem;
  opacity: 0.5;
  margin-bottom: 1.5rem;
}

.empty-container {
  min-height: 400px;
}

.recent-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.recent-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: rgba(255, 245, 245, 0.5);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.recent-item:hover {
  background: rgba(255, 230, 230, 0.7);
}

.recent-date {
  font-size: 0.9rem;
  color: #8B5A6B;
  font-weight: 500;
}

.recent-emotion {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.emotion-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  color: #8B5A6B;
  font-weight: 500;
}

.intensity-text {
  font-size: 0.8rem;
  color: #B8A8A8;
}

.topics-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.topic-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(255, 245, 245, 0.5);
  border-radius: 12px;
  transition: all 0.2s ease;
}

.topic-item:hover {
  background: rgba(255, 230, 230, 0.7);
  transform: translateX(4px);
}

.topic-rank {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #FFB6C1 0%, #FFA07A 100%);
  color: white;
  border-radius: 50%;
  font-weight: 700;
  font-size: 1.1rem;
}

.topic-info {
  flex: 1;
}

.topic-name {
  font-size: 1rem;
  font-weight: 600;
  color: #8B5A6B;
  margin-bottom: 0.25rem;
}

.topic-count {
  font-size: 0.85rem;
  color: #B8A8A8;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.25rem;
  background: rgba(255, 245, 245, 0.5);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.action-item:hover {
  background: rgba(255, 230, 230, 0.7);
  border-color: rgba(255, 182, 193, 0.5);
  transform: translateX(4px);
}

.action-icon {
  font-size: 2rem;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
}

.action-icon-1 {
  background: linear-gradient(135deg, #FFE5E5 0%, #FFD4D4 100%);
}

.action-icon-2 {
  background: linear-gradient(135deg, #E5F3FF 0%, #D4E9FF 100%);
}

.action-icon-3 {
  background: linear-gradient(135deg, #FFF5E5 0%, #FFE9D4 100%);
}

.action-content {
  flex: 1;
}

.action-title {
  font-size: 1rem;
  font-weight: 600;
  color: #8B5A6B;
  margin-bottom: 0.25rem;
}

.action-desc {
  font-size: 0.85rem;
  color: #B8A8A8;
  line-height: 1.4;
}

.action-arrow {
  font-size: 1.5rem;
  color: #FFB6C1;
  font-weight: bold;
}

.warm-button {
  background: linear-gradient(135deg, #FFB6C1 0%, #FFA07A 100%) !important;
  border: none !important;
  border-radius: 16px !important;
  box-shadow: 0 4px 15px rgba(255, 182, 193, 0.3) !important;
  transition: all 0.3s ease !important;
  font-weight: 600 !important;
}

.warm-button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 6px 20px rgba(255, 182, 193, 0.4) !important;
}

.warm-button :deep(.n-button__content) {
  color: white;
}

.warm-button-small :deep(.n-button) {
  border-color: rgba(255, 182, 193, 0.3);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.warm-button-small :deep(.n-button:hover) {
  border-color: rgba(255, 182, 193, 0.5);
  transform: translateY(-1px);
}

.warm-button-small :deep(.n-button--primary-type) {
  background: linear-gradient(135deg, #FFB6C1 0%, #FFA07A 100%) !important;
  border-color: transparent !important;
  box-shadow: 0 2px 8px rgba(255, 182, 193, 0.25) !important;
}

:deep(.n-card-header) {
  border-bottom: 1px solid rgba(255, 182, 193, 0.2);
  padding-bottom: 1rem;
  margin-bottom: 1rem;
}

:deep(.n-card-header__main) {
  color: #8B5A6B;
  font-weight: 600;
  font-size: 1.1rem;
}
</style>
