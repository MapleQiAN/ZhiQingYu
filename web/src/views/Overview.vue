<template>
  <div class="dashboard-page">
    <!-- Header Section -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">{{ $t('common.appName') }}</h1>
        <p class="page-subtitle">{{ $t('overview.subtitle') }}</p>
      </div>
      <div class="header-actions">
        <n-button type="primary" @click="loadStats" :loading="loading">
          <template #icon>
            <n-icon><RefreshOutline /></n-icon>
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
              @click="setDays(d)"
            >
              {{ d }}{{ $t('common.days') }}
            </n-button>
          </n-button-group>
        </div>
      </div>
    </div>

    <n-spin :show="loading">
      <template v-if="stats">
        <!-- Statistics Cards -->
        <div class="stats-grid">
          <div class="stat-card" :style="{ '--card-color': '#D9779F' }">
            <div class="stat-icon" style="background: linear-gradient(135deg, #D9779F, #C97A9A);">
              <n-icon size="32"><CalendarOutline /></n-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">{{ $t('overview.totalDays') }}</div>
              <div class="stat-value">
                <n-number-animation :from="0" :to="days" :duration="1000" />
              </div>
              <div class="stat-footer">
                <span class="stat-desc">{{ $t('overview.totalDaysDesc') }}</span>
              </div>
            </div>
          </div>

          <div class="stat-card" :style="{ '--card-color': '#FFB6C1' }">
            <div class="stat-icon" style="background: linear-gradient(135deg, #FFB6C1, #FFA07A);">
              <n-icon size="32"><ChatbubbleEllipsesOutline /></n-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">{{ $t('overview.emotionRecords') }}</div>
              <div class="stat-value">
                <n-number-animation :from="0" :to="emotionRecordsCount" :duration="1000" />
              </div>
              <div class="stat-footer">
                <span class="stat-desc">{{ $t('overview.emotionRecordsDesc') }}</span>
              </div>
            </div>
          </div>

          <div class="stat-card" :style="{ '--card-color': '#FFD4A3' }">
            <div class="stat-icon" style="background: linear-gradient(135deg, #FFD4A3, #FFC97A);">
              <n-icon size="32"><HeartOutline /></n-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">{{ $t('overview.emotionTypes') }}</div>
              <div class="stat-value">
                <n-number-animation :from="0" :to="emotionTypesCount" :duration="1000" />
              </div>
              <div class="stat-footer">
                <span class="stat-desc">{{ $t('overview.emotionTypesDesc') }}</span>
              </div>
            </div>
          </div>

          <div class="stat-card" :style="{ '--card-color': '#D4B3FF' }">
            <div class="stat-icon" style="background: linear-gradient(135deg, #D4B3FF, #C9A6FF);">
              <n-icon size="32"><TrendingUpOutline /></n-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">{{ $t('overview.emotionScore') }}</div>
              <div class="stat-value">
                <n-number-animation :from="0" :to="parseFloat(trendPercentage)" :duration="1000" :precision="1" />
              </div>
              <div class="stat-footer">
                <n-icon :component="TrendingUpOutline" class="trend-icon" />
                <span class="stat-desc trend-up">{{ $t('overview.trendGrowth') }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Charts and Info Section -->
        <div class="content-grid">
          <!-- Left: Emotion Type Distribution -->
          <div class="chart-section">
            <div class="section-header">
              <n-icon size="20"><PieChartOutline /></n-icon>
              <h3>{{ $t('overview.emotionTypeDistribution') }}</h3>
            </div>
            <div class="chart-container">
              <v-chart
                v-if="!loading && emotionData.length > 0"
                :option="pieChartOption"
                style="width: 100%; height: 350px"
              />
              <n-empty v-else-if="!loading" :description="$t('common.noData')" size="small" />
              <n-spin v-else size="small" />
            </div>
          </div>

          <!-- Middle: Top Topics -->
          <div class="info-section">
            <div class="section-header">
              <n-icon size="20"><TrophyOutline /></n-icon>
              <h3>{{ $t('overview.coreEmotionRanking') }}</h3>
            </div>
            <div class="concepts-list">
              <n-scrollbar style="max-height: 350px;">
                <div v-if="stats.top_topics && stats.top_topics.length > 0">
                  <div
                    v-for="(item, index) in stats.top_topics"
                    :key="index"
                    class="concept-item"
                  >
                    <div class="concept-rank" :class="`rank-${index + 1}`">{{ index + 1 }}</div>
                    <div class="concept-info">
                      <div class="concept-name">{{ item.topic }}</div>
                    </div>
                    <div class="concept-connections">
                      <n-tag :bordered="false" type="warning" size="small">
                        {{ item.count }} {{ $t('overview.emotionRecords') }}
                      </n-tag>
                    </div>
                  </div>
                </div>
                <n-empty v-else :description="$t('overview.noEmotionData')" size="small" />
              </n-scrollbar>
            </div>
          </div>

          <!-- Right: Quick Actions -->
          <div class="actions-section">
            <div class="section-header">
              <n-icon size="20"><RocketOutline /></n-icon>
              <h3>{{ $t('overview.quickActions') }}</h3>
            </div>
            <div class="quick-actions">
              <div class="action-card" @click="goToChat">
                <div class="action-icon" style="background: linear-gradient(135deg, #D9779F, #C97A9A);">
                  <n-icon size="28"><ChatbubbleEllipsesOutline /></n-icon>
                </div>
                <div class="action-content">
                  <div class="action-title">{{ $t('overview.startChat') }}</div>
                  <div class="action-desc">{{ $t('overview.startChatDesc') }}</div>
                </div>
                <n-icon class="action-arrow" size="16"><ArrowForwardOutline /></n-icon>
              </div>

              <div class="action-card" @click="goToJournal">
                <div class="action-icon" style="background: linear-gradient(135deg, #FFB6C1, #FFA07A);">
                  <n-icon size="28"><BookOutline /></n-icon>
                </div>
                <div class="action-content">
                  <div class="action-title">{{ $t('overview.viewJournal') }}</div>
                  <div class="action-desc">{{ $t('overview.viewJournalDesc') }}</div>
                </div>
                <n-icon class="action-arrow" size="16"><ArrowForwardOutline /></n-icon>
              </div>

              <div class="action-card" @click="goToStats">
                <div class="action-icon" style="background: linear-gradient(135deg, #FFD4A3, #FFC97A);">
                  <n-icon size="28"><AnalyticsOutline /></n-icon>
                </div>
                <div class="action-content">
                  <div class="action-title">{{ $t('overview.viewStats') }}</div>
                  <div class="action-desc">{{ $t('overview.viewStatsDesc') }}</div>
                </div>
                <n-icon class="action-arrow" size="16"><ArrowForwardOutline /></n-icon>
              </div>
            </div>
          </div>
        </div>

        <!-- Recent Emotions Table -->
        <div class="table-section">
          <div class="section-header">
            <n-icon size="20"><TimeOutline /></n-icon>
            <h3>{{ $t('overview.recentEmotions') }}</h3>
          </div>
          <n-data-table
            :columns="emotionColumns"
            :data="recentEmotions"
            :bordered="false"
            :single-line="false"
            :loading="loading"
          />
        </div>
      </template>
      <template v-else>
        <div class="empty-container">
          <div class="empty-state-large">
            <div class="empty-icon-large">📊</div>
            <p>{{ $t('common.noData') }}</p>
          </div>
        </div>
      </template>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed, h } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { format, parseISO } from 'date-fns'
import {
  NButton,
  NButtonGroup,
  NIcon,
  NNumberAnimation,
  NSpin,
  NEmpty,
  NTag,
  NDataTable,
  NScrollbar,
} from 'naive-ui'
import { use } from 'echarts/core'
import { PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'

use([
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  CanvasRenderer,
])
import {
  RefreshOutline,
  CalendarOutline,
  ChatbubbleEllipsesOutline,
  HeartOutline,
  TrendingUpOutline,
  PieChartOutline,
  TrophyOutline,
  RocketOutline,
  ArrowForwardOutline,
  BookOutline,
  AnalyticsOutline,
  TimeOutline,
} from '@vicons/ionicons5'
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
      recentEmotions.value = response.data.items.slice(0, 10).reverse()
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

const getPieColor = (index: number) => {
  const colors = ['#D9779F', '#FFB6C1', '#FFD4A3', '#D4B3FF', '#B3D9FF', '#FFB3BA', '#B3FFB3', '#B3E5D1']
  return colors[index % colors.length]
}

const formatDate = (dateStr: string) => {
  try {
    return format(parseISO(dateStr), 'yyyy-MM-dd')
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

// ECharts 饼图配置
const pieChartOption = computed(() => {
  if (!emotionData.value || emotionData.value.length === 0) {
    return {}
  }

  return {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}% ({d}%)',
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      formatter: (name: string) => {
        const item = emotionData.value.find((d) => d.emotion === name)
        return item ? `${name}: ${item.value}%` : name
      },
    },
    series: [
      {
        name: t('overview.emotionTypeDistribution'),
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['40%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: {
          show: false,
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold',
          },
        },
        data: emotionData.value.map((item, index) => ({
          value: item.value,
          name: item.emotion,
          itemStyle: {
            color: getPieColor(index),
          },
        })),
      },
    ],
  }
})

// Emotion Table Columns
const emotionColumns = [
  {
    title: t('overview.fileName'),
    key: 'date',
    width: 150,
    render: (row: DailySummaryItem) => {
      return h('div', { style: 'display: flex; align-items: center; gap: 8px;' }, [
        h('span', { style: 'font-weight: 500;' }, formatDate(row.date))
      ])
    }
  },
  {
    title: t('overview.type'),
    key: 'main_emotion',
    width: 120,
    render: (row: DailySummaryItem) => {
      const emotion = row.main_emotion
      const color = getEmotionColor(emotion)
      return h(NTag, {
        type: 'info',
        size: 'small',
        bordered: false,
        style: { backgroundColor: color, color: '#8B5A6B' }
      }, { default: () => getEmotionLabel(emotion) })
    }
  },
  {
    title: t('overview.intensity'),
    key: 'avg_intensity',
    width: 100,
    render: (row: DailySummaryItem) => {
      return h('span', row.avg_intensity ? row.avg_intensity.toFixed(1) : '-')
    }
  },
  {
    title: t('overview.time'),
    key: 'date',
    width: 180,
    render: (row: DailySummaryItem) => {
      return h('span', formatDate(row.date))
    }
  },
  {
    title: t('overview.operation'),
    key: 'actions',
    width: 120,
    render: (row: DailySummaryItem) => {
      return h('div', { style: 'display: flex; gap: 8px;' }, [
        h(NButton, {
          size: 'small',
          type: 'primary',
          text: true,
          onClick: () => handleViewDetail(row)
        }, { default: () => t('overview.view') })
      ])
    }
  }
]

// Methods
const handleViewDetail = (row: DailySummaryItem) => {
  router.push(`/journal?date=${row.date}`)
}

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

<style lang="scss" scoped>
.dashboard-page {
  padding: 0;
  background: transparent;
  min-height: calc(100vh - 100px);
  position: relative;

  // 统一按钮样式
  :deep(.n-button) {
    border: none !important;

    &:focus {
      outline: none;
      box-shadow: 0 0 0 2px rgba(217, 119, 159, 0.2);
    }
  }

  :deep(.n-button--primary-type) {
    background: linear-gradient(135deg, #D9779F 0%, #C97A9A 100%) !important;
    border: none !important;
    box-shadow: 0 2px 8px rgba(217, 119, 159, 0.3);
    color: white;

    &:hover {
      background: linear-gradient(135deg, #C97A9A 0%, #B86A8A 100%) !important;
      box-shadow: 0 4px 12px rgba(217, 119, 159, 0.4);
      transform: translateY(-1px);
    }

    &:active {
      background: linear-gradient(135deg, #B86A8A 0%, #A85A7A 100%) !important;
      transform: translateY(0);
    }

    &:focus {
      outline: none;
      box-shadow: 0 0 0 2px rgba(217, 119, 159, 0.3);
    }
  }

  :deep(.n-button--default-type) {
    background: white;
    border: 1px solid #e0e0e0 !important;
    color: #666;

    &:hover {
      background: #fafafa;
      border-color: #D9779F !important;
      color: #D9779F;
      transform: translateY(-1px);
    }

    &:active {
      background: #f0f0f0;
      transform: translateY(0);
    }

    &:focus {
      outline: none;
      border-color: #D9779F !important;
      box-shadow: 0 0 0 2px rgba(217, 119, 159, 0.2);
    }
  }
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
  padding: 0;
  position: relative;
  z-index: 1;
}

.header-content {
  flex: 1;

  .page-title {
    font-size: 32px;
    font-weight: 700;
    margin: 0 0 8px 0;
    background: linear-gradient(135deg, #D9779F 0%, #C97A9A 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .page-subtitle {
    font-size: 14px;
    color: #666;
    margin: 0;
  }
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
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

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-bottom: 32px;
}

.stat-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  border: 2px solid transparent;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--card-color), transparent);
    transform: translateX(-100%);
    transition: transform 0.5s ease;
  }

  &:hover {
    border-color: var(--card-color);
    box-shadow: 0 4px 20px rgba(217, 119, 159, 0.3);
    transform: translateY(-4px);
  }

  &:hover::before {
    transform: translateX(0);
  }

  .stat-icon {
    width: 64px;
    height: 64px;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    flex-shrink: 0;
    box-shadow: 0 4px 12px rgba(217, 119, 159, 0.3);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
  }

  .stat-card:hover .stat-icon {
    transform: scale(1.1) rotate(5deg);
    box-shadow: 0 6px 20px rgba(217, 119, 159, 0.4);
  }

  .stat-icon::after {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.3) 0%, transparent 70%);
    opacity: 0;
    transition: opacity 0.3s ease;
  }

  .stat-card:hover .stat-icon::after {
    opacity: 1;
  }

  .stat-content {
    flex: 1;
    min-width: 0;

    .stat-label {
      font-size: 14px;
      color: #999;
      margin-bottom: 8px;
    }

    .stat-value {
      font-size: 32px;
      font-weight: 700;
      color: #333;
      line-height: 1;
      margin-bottom: 8px;
    }

    .stat-footer {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 12px;

      .stat-desc {
        color: #666;

        &.trend-up {
          color: #52c41a;
          font-weight: 600;
        }
      }

      .trend-icon {
        color: #52c41a;
      }
    }
  }
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 24px;
  margin-bottom: 32px;
}

.chart-section,
.info-section,
.actions-section {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: 2px solid transparent;
  transition: all 0.3s ease;

  &:hover {
    border-color: rgba(217, 119, 159, 0.3);
    box-shadow: 0 4px 20px rgba(217, 119, 159, 0.15);
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 2px solid #f0f0f0;

    h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: #333;
    }

    .n-icon {
      color: #D9779F;
    }
  }
}

.chart-container {
  height: 350px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.concepts-list {
  .concept-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 8px;
    background: #fafafa;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;

    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 3px;
      background: linear-gradient(180deg, #D9779F 0%, #C97A9A 100%);
      transform: scaleY(0);
      transition: transform 0.3s ease;
    }

    &:hover {
      background: linear-gradient(135deg, rgba(217, 119, 159, 0.1), rgba(201, 122, 154, 0.1));
      transform: translateX(4px);
    }

    &:hover::before {
      transform: scaleY(1);
    }

    .concept-rank {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 14px;
      background: #e0e0e0;
      color: #666;

      &.rank-1 {
        background: linear-gradient(135deg, #D9779F, #C97A9A);
        color: white;
      }

      &.rank-2 {
        background: linear-gradient(135deg, #FFB6C1, #FFA07A);
        color: white;
      }

      &.rank-3 {
        background: linear-gradient(135deg, #FFD4A3, #FFC97A);
        color: white;
      }
    }

    .concept-info {
      flex: 1;
      min-width: 0;

      .concept-name {
        font-weight: 600;
        font-size: 14px;
        color: #333;
        margin-bottom: 4px;
      }
    }

    .concept-connections {
      flex-shrink: 0;
    }
  }
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;

  .action-card {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px;
    border-radius: 12px;
    background: #fafafa;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    border: 2px solid transparent;
    position: relative;
    overflow: hidden;

    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: -100%;
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, transparent, rgba(217, 119, 159, 0.1), transparent);
      transition: left 0.5s ease;
    }

    &:hover {
      background: white;
      border-color: rgba(217, 119, 159, 0.5);
      box-shadow: 0 4px 16px rgba(217, 119, 159, 0.2);
      transform: translateX(4px);
    }

    &:hover::before {
      left: 100%;
    }

    &:hover .action-arrow {
      transform: translateX(4px);
    }

    .action-icon {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      flex-shrink: 0;
      box-shadow: 0 4px 12px rgba(217, 119, 159, 0.3);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .action-card:hover .action-icon {
      transform: scale(1.1) rotate(5deg);
      box-shadow: 0 6px 18px rgba(217, 119, 159, 0.4);
    }

    .action-content {
      flex: 1;

      .action-title {
        font-weight: 600;
        font-size: 14px;
        color: #333;
        margin-bottom: 4px;
      }

      .action-desc {
        font-size: 12px;
        color: #999;
      }
    }

    .action-arrow {
      color: #D9779F;
      transition: transform 0.3s ease;
    }
  }
}

.table-section {
  background: white;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: 2px solid transparent;
  transition: all 0.3s ease;

  &:hover {
    border-color: rgba(217, 119, 159, 0.3);
    box-shadow: 0 4px 20px rgba(217, 119, 159, 0.15);
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 2px solid #f0f0f0;

    h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: #333;
    }

    .n-icon {
      color: #D9779F;
    }
  }
}

.empty-container {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  position: relative;
  z-index: 1;
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

:deep(.n-data-table) {
  .n-data-table-th {
    background: linear-gradient(135deg, rgba(217, 119, 159, 0.1), rgba(201, 122, 154, 0.1));
    color: #D9779F;
    font-weight: 600;
  }

  .n-data-table-tr:hover {
    background: linear-gradient(135deg, rgba(217, 119, 159, 0.05), rgba(201, 122, 154, 0.05));
  }
}

@media (max-width: 1440px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .dashboard-page {
    padding: 0;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
  }

  .header-actions {
    width: 100%;
    flex-direction: column;

    .time-selector {
      width: 100%;
      justify-content: space-between;
    }
  }
}
</style>

