<template>
  <div class="space-y-8">
    <!-- 时间选择器 -->
    <n-card>
      <div class="flex items-center space-x-4">
        <span class="text-sm text-gray-600">{{ $t('overview.statsDays') }}:</span>
        <div class="flex space-x-2">
          <n-button
            v-for="d in [7, 14, 30]"
            :key="d"
            :type="days === d ? 'primary' : 'default'"
            size="small"
            @click="setDays(d)"
          >
            {{ d }}{{ $t('common.days') }}
          </n-button>
        </div>
      </div>
    </n-card>

    <n-spin :show="loading">
      <div v-if="stats">
        <!-- 情绪趋势图 -->
        <n-card class="mb-6">
          <h2 class="text-lg font-semibold mb-4">{{ $t('overview.emotionTrend') }}</h2>
          <div style="width: 100%; height: 300px">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart :data="trendData">
                <CartesianGrid stroke-dasharray="3 3" />
                <XAxis :data-key="'date'" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  data-key="score"
                  stroke="#3b82f6"
                  :stroke-width="2"
                  :name="$t('overview.emotionScore')"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </n-card>

        <!-- 情绪分布图 -->
        <n-card class="mb-6">
          <h2 class="text-lg font-semibold mb-4">{{ $t('overview.emotionDistribution') }}</h2>
          <div style="width: 100%; height: 300px">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart :data="emotionData">
                <CartesianGrid stroke-dasharray="3 3" />
                <XAxis :data-key="'emotion'" />
                <YAxis />
                <Tooltip />
                <Bar data-key="value" fill="#3b82f6" :name="$t('overview.percentage')" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </n-card>

        <!-- 热门主题 -->
        <n-card>
          <h2 class="text-lg font-semibold mb-4">{{ $t('overview.topTopics') }}</h2>
          <div v-if="stats.top_topics.length === 0" class="text-gray-500 text-center py-8">
            {{ $t('common.noData') }}
          </div>
          <div v-else class="flex flex-wrap gap-3">
            <n-tag
              v-for="(item, index) in stats.top_topics"
              :key="index"
              type="info"
              size="medium"
            >
              {{ item.topic }} ({{ item.count }})
            </n-tag>
          </div>
        </n-card>
      </div>
      <div v-else class="text-center py-12 text-gray-500">
        {{ $t('common.noData') }}
      </div>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  NCard,
  NButton,
  NSpin,
  NTag,
} from 'naive-ui'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { getStatsOverview, type EmotionStatsOverview } from '@/lib/api'

const { t } = useI18n()

const stats = ref<EmotionStatsOverview | null>(null)
const loading = ref(true)
const days = ref(7)

onMounted(() => {
  loadStats()
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

const setDays = (d: number) => {
  days.value = d
}

const getEmotionLabel = (emotion: string) => {
  const emotionKey = emotion as keyof typeof import('@/i18n/zh').default.emotions
  try {
    return t(`emotions.${emotionKey}`) || emotion
  } catch {
    return emotion
  }
}

// 格式化趋势数据（只显示日期）
const trendData = computed(() => {
  if (!stats.value) return []
  return stats.value.trend.map((item) => ({
    ...item,
    date: item.date.split('T')[0].slice(5), // 只显示月-日
  }))
})

// 格式化情绪分布数据
const emotionData = computed(() => {
  if (!stats.value) return []
  return Object.entries(stats.value.emotion_distribution).map(
    ([emotion, value]) => ({
      emotion: getEmotionLabel(emotion),
      value: Number((value * 100).toFixed(1)),
    })
  )
})
</script>

<style scoped>
.space-y-8 > * + * {
  margin-top: 2rem;
}

.space-y-4 > * + * {
  margin-top: 1rem;
}

.space-x-2 > * + * {
  margin-left: 0.5rem;
}

.space-x-4 > * + * {
  margin-left: 1rem;
}

.flex {
  display: flex;
}

.flex-wrap {
  flex-wrap: wrap;
}

.items-center {
  align-items: center;
}

.gap-3 {
  gap: 0.75rem;
}
</style>

