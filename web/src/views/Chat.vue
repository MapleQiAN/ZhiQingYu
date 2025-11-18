<template>
  <div class="chat-layout">
    <!-- 左侧边栏：历史聊天记录 -->
    <div class="sidebar" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
      <div class="sidebar-header">
        <n-button
          quaternary
          circle
          size="small"
          @click="sidebarCollapsed = !sidebarCollapsed"
          class="sidebar-toggle"
        >
          <template #icon>
            <span>{{ sidebarCollapsed ? '→' : '←' }}</span>
          </template>
        </n-button>
        <n-button
          type="primary"
          @click="handleNewChat"
          class="new-chat-button"
          :disabled="loading"
        >
          <template #icon>
            <span>➕</span>
          </template>
          {{ $t('chat.newChat') }}
        </n-button>
      </div>
      <div v-if="!sidebarCollapsed" class="sidebar-content">
        <div class="sidebar-title">{{ $t('chat.chatHistory') }}</div>
        <div v-if="loadingSessions" class="sidebar-loading">
          {{ $t('chat.loadingHistory') }}
        </div>
        <div v-else-if="sessions.length === 0" class="sidebar-empty">
          {{ $t('chat.noHistory') }}
        </div>
        <div v-else class="session-list">
          <div
            v-for="session in sessions"
            :key="session.id"
            :class="['session-item', { active: session.id === sessionId }]"
            @click="handleSwitchSession(session.id)"
          >
            <div class="session-content">
              <div class="session-preview">{{ session.preview || $t('chat.newChat') }}</div>
              <div class="session-time">
                {{ formatSessionTime(session.latest_message_at || session.created_at) }}
              </div>
            </div>
            <n-button
              quaternary
              circle
              size="small"
              class="session-delete-button"
              @click.stop="handleDeleteSession(session.id)"
              :disabled="loading"
            >
              <template #icon>
                <span>🗑️</span>
              </template>
            </n-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 主聊天区域 -->
    <div class="chat-container">
      <!-- 顶部：今日主情绪 -->
      <n-card class="emotion-card" hoverable>
        <div class="emotion-card-content">
          <div class="emotion-left">
            <div class="emotion-icon-wrapper">
              <div class="emotion-icon">💭</div>
            </div>
            <span class="emotion-label">{{ $t('chat.todayEmotion') }}</span>
          </div>
          <div class="emotion-badge">
            <span class="emotion-text">
              {{ todayEmotion ? getEmotionLabel(todayEmotion) : $t('chat.noEmotion') }}
            </span>
          </div>
        </div>
      </n-card>

      <!-- 聊天记录区域 -->
      <div class="messages-container">
      <div v-if="messages.length === 0" class="welcome-section">
        <div class="welcome-icon">🌺</div>
        <p class="welcome-title">{{ $t('chat.welcome') }}</p>
        <p class="welcome-desc">{{ $t('chat.welcomeDesc') }}</p>
      </div>

      <div
        v-for="(msg, index) in messages"
        :key="index"
        :class="['message-wrapper', msg.role === 'user' ? 'user-message' : 'assistant-message']"
      >
        <!-- 用户消息：普通气泡 -->
        <div
          v-if="msg.role === 'user'"
          :class="[
            'message-bubble',
            'user-bubble',
          ]"
        >
          <p class="message-content">{{ msg.content }}</p>
        </div>
        
        <!-- AI回复：如果有卡片数据则显示卡片，否则显示普通气泡 -->
        <div v-else>
          <HeartCard
            v-if="msg.card_data && hasCardData(msg.card_data)"
            :card-data="msg.card_data"
            class="assistant-card"
          />
          <div
            v-else
            :class="[
              'message-bubble',
              'assistant-bubble',
            ]"
          >
            <p class="message-content">{{ msg.content }}</p>
          </div>
        </div>
      </div>

      <div v-if="loading" class="message-wrapper assistant-message">
        <div class="message-bubble assistant-bubble loading-bubble">
          <div class="loading-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
          <span class="loading-text">{{ $t('chat.sending') }}</span>
        </div>
      </div>

      <div ref="messagesEndRef" />
    </div>

    <!-- 输入区域 -->
    <n-card class="input-card">
      <!-- 体验模式选择器 -->
      <div v-if="messages.length === 0" class="experience-mode-selector">
        <div class="mode-label">{{ $t('chat.experienceMode') }}</div>
        <div class="mode-buttons">
          <n-button
            v-for="mode in experienceModes"
            :key="mode.value"
            :type="selectedExperienceMode === mode.value ? 'primary' : 'default'"
            :ghost="selectedExperienceMode !== mode.value"
            size="small"
            @click="selectedExperienceMode = mode.value"
            class="mode-button"
          >
            <template #icon>
              <span>{{ mode.icon }}</span>
            </template>
            {{ mode.label }}
          </n-button>
        </div>
      </div>
      
      <!-- 风险级别警告 -->
      <div v-if="lastRiskLevel === 'high'" class="risk-warning">
        <n-alert type="warning" :title="$t('chat.riskWarning')" :show-icon="true">
          {{ $t('chat.riskWarningDesc') }}
        </n-alert>
      </div>
      
      <div class="input-wrapper">
        <n-input
          v-model:value="input"
          type="textarea"
          :placeholder="$t('chat.inputPlaceholder')"
          :rows="3"
          :disabled="loading"
          @keydown="handleKeyPress"
          class="chat-input"
          :autosize="{ minRows: 2, maxRows: 5 }"
          :status="undefined"
        />
        <n-button
          type="primary"
          :loading="loading"
          :disabled="!input.trim()"
          @click="handleSend"
          class="send-button"
          size="large"
        >
          <template #icon>
            <span class="send-icon">✨</span>
          </template>
          {{ $t('common.send') }}
        </n-button>
      </div>
    </n-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { NCard, NInput, NButton, NAlert, useMessage, useDialog } from 'naive-ui'
import {
  sendChatMessage,
  getSessions,
  getSessionMessages,
  deleteSession,
  type ChatMessage,
  type SessionItem,
  type CardData,
} from '@/lib/api'
import HeartCard from '@/components/HeartCard.vue'

const { t } = useI18n()
const message = useMessage()
const dialog = useDialog()

const messages = ref<ChatMessage[]>([])
const input = ref('')
const loading = ref(false)
const sessionId = ref<string | null>(null)
const todayEmotion = ref<string | null>(null)
const messagesEndRef = ref<HTMLDivElement | null>(null)
const sidebarCollapsed = ref(false)
const sessions = ref<SessionItem[]>([])
const loadingSessions = ref(false)
const selectedExperienceMode = ref<'A' | 'B' | 'C' | 'D' | null>(null)
const lastRiskLevel = ref<'normal' | 'high'>('normal')

// 体验模式选项（使用computed确保国际化文本正确更新）
const experienceModes = computed(() => [
  { value: 'A' as const, label: t('chat.modeA'), icon: '👂' },
  { value: 'B' as const, label: t('chat.modeB'), icon: '💡' },
  { value: 'C' as const, label: t('chat.modeC'), icon: '💪' },
  { value: 'D' as const, label: t('chat.modeD'), icon: '🌊' },
])

const scrollToBottom = async () => {
  await nextTick()
  messagesEndRef.value?.scrollIntoView({ behavior: 'smooth' })
}

onMounted(() => {
  scrollToBottom()
  loadSessions()
})

// 加载会话列表
const loadSessions = async () => {
  loadingSessions.value = true
  try {
    const response = await getSessions()
    if (response.error) {
      console.error('Failed to load sessions:', response.error)
      return
    }
    if (response.data) {
      sessions.value = response.data.sessions
    }
  } catch (error) {
    console.error('Error loading sessions:', error)
  } finally {
    loadingSessions.value = false
  }
}

// 切换会话
const handleSwitchSession = async (id: string) => {
  if (id === sessionId.value) return

  loading.value = true
  try {
    const response = await getSessionMessages(id)
    if (response.error) {
      message.error(`${t('common.error')}: ${response.error.message}`)
      return
    }
    if (response.data) {
      sessionId.value = id
      messages.value = response.data.messages
      todayEmotion.value = null // 重置情绪，因为不同会话的情绪可能不同
      lastRiskLevel.value = 'normal' // 重置风险级别
      selectedExperienceMode.value = null // 重置体验模式
      scrollToBottom()
    }
  } catch (error) {
    console.error('Error loading session messages:', error)
    message.error(t('chat.sendFailed'))
  } finally {
    loading.value = false
  }
}

// 新建对话
const handleNewChat = () => {
  sessionId.value = null
  messages.value = []
  todayEmotion.value = null
  input.value = ''
  selectedExperienceMode.value = null
  lastRiskLevel.value = 'normal'
}

// 删除会话
const handleDeleteSession = async (id: string) => {
  dialog.warning({
    title: t('common.confirm'),
    content: t('chat.deleteConfirm'),
    positiveText: t('common.confirm'),
    negativeText: t('common.cancel'),
    onPositiveClick: async () => {
      try {
        const response = await deleteSession(id)
        if (response.error) {
          message.error(`${t('common.error')}: ${response.error.message}`)
          return
        }

        // 如果删除的是当前会话，清空当前会话
        if (id === sessionId.value) {
          handleNewChat()
        }

        // 刷新会话列表
        await loadSessions()
        message.success(t('chat.deleteSuccess'))
      } catch (error) {
        console.error('Error deleting session:', error)
        message.error(t('chat.deleteFailed'))
      }
    },
  })
}

// 格式化会话时间
const formatSessionTime = (timeStr: string | null) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) {
    // 今天，显示时间
    const hours = date.getHours()
    const minutes = date.getMinutes()
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`
  } else if (days === 1) {
    return t('common.yesterday')
  } else if (days < 7) {
    return `${days}${t('common.days')}前`
  } else {
    // 超过7天，显示日期
    const month = date.getMonth() + 1
    const day = date.getDate()
    return `${month}/${day}`
  }
}

// 检查卡片数据是否有效
const hasCardData = (cardData: CardData | null | undefined): boolean => {
  if (!cardData) return false
  // 检查5步骤内容
  if (
    cardData.step1_emotion_mirror ||
    cardData.step1_problem_restate ||
    cardData.step2_breakdown ||
    cardData.step3_explanation ||
    cardData.step4_suggestions ||
    cardData.step5_summary
  ) {
    return true
  }
  // 检查旧版格式
  return !!(
    cardData.theme ||
    cardData.emotion_echo ||
    cardData.clarification ||
    (cardData.suggestion && 
      (Array.isArray(cardData.suggestion) ? cardData.suggestion.length > 0 : cardData.suggestion.trim().length > 0))
  )
}

// 监听会话变化，自动刷新会话列表
watch(sessionId, () => {
  loadSessions()
})

const handleSend = async () => {
  if (!input.value.trim() || loading.value) return

  const userMessage: ChatMessage = {
    role: 'user',
    content: input.value.trim(),
  }

  const newMessages = [...messages.value, userMessage]
  messages.value = newMessages
  const currentInput = input.value.trim()
  input.value = ''
  loading.value = true

  try {
    const response = await sendChatMessage({
      session_id: sessionId.value,
      messages: newMessages,
      experience_mode: selectedExperienceMode.value,
    })

    if (response.error) {
      console.error('API Error:', response.error)
      message.error(`${t('common.error')}: ${response.error.message}`)
      // 恢复输入
      input.value = currentInput
      return
    }

    if (response.data) {
      const data = response.data
      sessionId.value = data.session_id
      todayEmotion.value = data.emotion
      lastRiskLevel.value = data.risk_level

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: data.reply,
        card_data: data.card_data || null,
      }

      messages.value = [...newMessages, assistantMessage]
      scrollToBottom()
      // 刷新会话列表
      loadSessions()
      
      // 如果检测到高风险，显示额外提示
      if (data.risk_level === 'high') {
        message.warning(t('chat.highRiskDetected'))
      }
    }
  } catch (error) {
    console.error('Request failed:', error)
    message.error(t('chat.sendFailed'))
    // 恢复输入
    input.value = currentInput
  } finally {
    loading.value = false
  }
}

const handleKeyPress = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
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
</script>

<style scoped>
@import '../styles/design-system.css';

.chat-layout {
  display: flex;
  height: calc(100vh - 180px);
  min-height: 600px;
  gap: var(--spacing-md);
}

.sidebar {
  width: 280px;
  min-width: 280px;
  background: var(--bg-elevated);
  border: var(--border-width-thin) solid var(--border-color-light);
  border-radius: var(--radius-2xl);
  box-shadow: var(--shadow-warm-md);
  backdrop-filter: blur(20px);
  display: flex;
  flex-direction: column;
  transition: all var(--transition-base);
  overflow: hidden;
}

.sidebar-collapsed {
  width: 60px;
  min-width: 60px;
}

.sidebar-header {
  padding: var(--spacing-md);
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
  border-bottom: var(--border-width-thin) solid var(--border-color-light);
  flex-shrink: 0;
}

.sidebar-toggle {
  flex-shrink: 0;
}

.new-chat-button {
  flex: 1;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%) !important;
  border: none !important;
  border-color: transparent !important;
  border-radius: var(--radius-lg) !important;
  font-weight: var(--font-weight-semibold);
  transition: all var(--transition-base);
  outline: none !important;
}

/* 移除新对话按钮的所有边框和验证状态边框 */
.new-chat-button :deep(.n-button__border),
.new-chat-button :deep(.n-button__state-border),
.new-chat-button :deep(.n-button__border--focus),
.new-chat-button :deep(.n-button__border--hover),
.new-chat-button :deep(.n-button__border--active),
.new-chat-button :deep(.n-button__border--success),
.new-chat-button :deep(.n-button__border--warning),
.new-chat-button :deep(.n-button__border--error) {
  border: none !important;
  border-color: transparent !important;
  display: none !important;
}

.new-chat-button :deep(button),
.new-chat-button :deep(.n-button),
.new-chat-button :deep(.n-button *) {
  border: none !important;
  border-color: transparent !important;
  outline: none !important;
}

.new-chat-button :deep(button:focus),
.new-chat-button :deep(button:focus-visible),
.new-chat-button :deep(.n-button--focus),
.new-chat-button :deep(.n-button--focus *) {
  border: none !important;
  border-color: transparent !important;
  outline: none !important;
  box-shadow: none !important;
}

.new-chat-button :deep(.n-button--success),
.new-chat-button :deep(.n-button--success *),
.new-chat-button :deep(.n-button--warning),
.new-chat-button :deep(.n-button--warning *),
.new-chat-button :deep(.n-button--error),
.new-chat-button :deep(.n-button--error *) {
  border: none !important;
  border-color: transparent !important;
  box-shadow: none !important;
}

.new-chat-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-warm-md) !important;
}

.new-chat-button:focus,
.new-chat-button:focus-visible {
  outline: none !important;
  box-shadow: var(--shadow-warm-md) !important;
}

.sidebar-collapsed .new-chat-button {
  display: none;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
}

.sidebar-content::-webkit-scrollbar {
  width: 6px;
}

.sidebar-content::-webkit-scrollbar-track {
  background: var(--color-neutral-100);
  border-radius: var(--radius-lg);
}

.sidebar-content::-webkit-scrollbar-thumb {
  background: var(--color-primary-light);
  border-radius: var(--radius-lg);
}

.sidebar-content::-webkit-scrollbar-thumb:hover {
  background: var(--color-primary);
}

.sidebar-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-md);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  opacity: 0.85;
}

.sidebar-loading,
.sidebar-empty {
  text-align: center;
  padding: var(--spacing-xl) var(--spacing-md);
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-normal);
}

.session-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.session-item {
  padding: var(--spacing-md) var(--spacing-md);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-base);
  border: var(--border-width-thin) solid transparent;
  background: var(--color-primary-lighter);
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
}

.session-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: linear-gradient(180deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  transform: scaleY(0);
  transition: transform var(--transition-base);
}

.session-item:hover {
  background: var(--color-primary-light);
  transform: translateX(4px);
  border-color: var(--border-color-base);
}

.session-item:hover::before {
  transform: scaleY(1);
}

.session-item.active {
  background: linear-gradient(135deg, var(--color-primary-lighter) 0%, var(--color-secondary-lighter) 100%);
  border-color: var(--border-color-base);
  box-shadow: var(--shadow-warm-sm);
}

.session-item.active::before {
  transform: scaleY(1);
}

.session-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.session-preview {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: var(--line-height-normal);
}

.session-item.active .session-preview {
  color: var(--text-primary);
  font-weight: var(--font-weight-semibold);
}

.session-time {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  font-weight: var(--font-weight-normal);
}

.session-item.active .session-time {
  color: var(--text-primary);
  font-weight: var(--font-weight-medium);
}

.session-delete-button {
  opacity: 0;
  transition: opacity var(--transition-base);
  flex-shrink: 0;
}

.session-item:hover .session-delete-button {
  opacity: 1;
}

.session-delete-button:hover {
  background-color: var(--color-error-lighter) !important;
  color: var(--color-error) !important;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  min-width: 0;
}

.emotion-card {
  background: var(--bg-elevated) !important;
  border: var(--border-width-thin) solid var(--border-color-light) !important;
  border-radius: var(--radius-2xl) !important;
  box-shadow: var(--shadow-warm-md) !important;
  transition: all var(--transition-smooth) !important;
  backdrop-filter: blur(20px);
  flex-shrink: 0;
  outline: none !important;
}

.emotion-card :deep(.n-card) {
  outline: none !important;
  border: none !important;
}

.emotion-card :deep(.n-card__content) {
  outline: none !important;
}

.emotion-card:hover {
  box-shadow: var(--shadow-warm-lg) !important;
  transform: translateY(-3px);
  border-color: var(--border-color-base) !important;
}

.emotion-card-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-sm) 0;
}

.emotion-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.emotion-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, var(--color-primary-lighter) 0%, var(--color-secondary-lighter) 100%);
  border-radius: var(--radius-xl);
  border: var(--border-width-thin) solid var(--border-color-light);
}

.emotion-icon {
  font-size: var(--font-size-2xl);
  filter: drop-shadow(0 2px 6px rgba(232, 180, 184, 0.4));
  animation: float 3s ease-in-out infinite;
}

.emotion-label {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  letter-spacing: 0.3px;
}

.emotion-badge {
  padding: var(--spacing-sm) var(--spacing-lg);
  background: linear-gradient(135deg, var(--color-primary-lighter) 0%, var(--color-secondary-lighter) 100%);
  border-radius: var(--radius-2xl);
  border: var(--border-width-thin) solid var(--border-color-base);
  box-shadow: var(--shadow-warm-sm);
  transition: all var(--transition-base);
}

.emotion-badge:hover {
  transform: scale(1.05);
  box-shadow: var(--shadow-warm-md);
}

.emotion-text {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  /* 使用更深的渐变以确保可读性 */
  background: linear-gradient(135deg, var(--color-primary-darker) 0%, var(--color-primary-dark) 50%, var(--color-primary-darker) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-lg) var(--spacing-md);
  scroll-behavior: smooth;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  min-height: 0;
}

.messages-container::-webkit-scrollbar {
  width: 8px;
}

.messages-container::-webkit-scrollbar-track {
  background: var(--color-neutral-100);
  border-radius: var(--radius-lg);
}

.messages-container::-webkit-scrollbar-thumb {
  background: var(--color-primary-light);
  border-radius: var(--radius-lg);
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background: var(--color-primary);
}

.welcome-section {
  text-align: center;
  padding: var(--spacing-3xl) var(--spacing-md);
  animation: welcomeFadeIn var(--transition-smooth);
}

@keyframes welcomeFadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.welcome-icon {
  font-size: var(--font-size-5xl);
  margin-bottom: var(--spacing-md);
  filter: drop-shadow(0 4px 8px rgba(232, 180, 184, 0.3));
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}

.welcome-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  margin-bottom: var(--spacing-md);
  /* 使用更深的渐变以确保可读性 */
  background: linear-gradient(135deg, var(--color-primary-darker) 0%, var(--color-primary-dark) 50%, var(--color-primary-darker) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.welcome-desc {
  font-size: var(--font-size-base);
  color: var(--text-secondary);
  line-height: var(--line-height-relaxed);
  font-weight: var(--font-weight-normal);
}

.message-wrapper {
  display: flex;
  animation: slideIn 0.3s ease;
  margin-bottom: var(--spacing-xs);
}

.message-wrapper:last-of-type {
  margin-bottom: 0;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-message {
  justify-content: flex-end;
  padding-left: var(--spacing-xl);
}

.assistant-message {
  justify-content: flex-start;
  padding-right: var(--spacing-xl);
}

.message-bubble {
  max-width: 75%;
  padding: var(--spacing-md) var(--spacing-lg);
  word-wrap: break-word;
  position: relative;
  box-shadow: var(--shadow-md);
  transition: all var(--transition-base);
  line-height: var(--line-height-relaxed);
  animation: messageSlideIn var(--transition-smooth);
  border-radius: var(--radius-2xl);
}

@keyframes messageSlideIn {
  from {
    opacity: 0;
    transform: translateY(10px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.message-bubble:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-lg);
}

.user-bubble {
  /* 使用更浅更温暖的渐变 */
  background: linear-gradient(135deg, var(--color-primary-dark) 0%, var(--color-primary) 50%, var(--color-secondary) 100%);
  color: var(--text-inverse);
  /* 精致的圆角：右上和左上大圆角，右下小圆角，左下中等圆角 */
  border-top-left-radius: var(--radius-2xl);
  border-top-right-radius: var(--radius-2xl);
  border-bottom-left-radius: var(--radius-lg);
  border-bottom-right-radius: var(--radius-md);
  box-shadow: var(--shadow-warm-md), 
              0 2px 8px rgba(232, 180, 184, 0.2);
  position: relative;
  overflow: hidden;
}

.user-bubble::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s ease;
}

.user-bubble:hover::before {
  left: 100%;
}

.assistant-bubble {
  background: var(--bg-elevated);
  color: var(--text-primary);
  border: var(--border-width-thin) solid var(--border-color-base);
  /* 精致的圆角：左上和左下大圆角，右上小圆角，右下中等圆角 */
  border-top-left-radius: var(--radius-2xl);
  border-top-right-radius: var(--radius-lg);
  border-bottom-left-radius: var(--radius-xl);
  border-bottom-right-radius: var(--radius-lg);
  backdrop-filter: blur(15px);
  box-shadow: var(--shadow-sm),
              0 1px 3px rgba(232, 180, 184, 0.08);
  position: relative;
}

.assistant-bubble::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, var(--color-primary-lighter) 0%, transparent 100%);
  pointer-events: none;
  border-radius: inherit;
  opacity: 0.15;
}

.message-content {
  margin: 0;
  line-height: 1.7;
  font-size: var(--font-size-base);
  white-space: pre-wrap;
  word-break: break-word;
  letter-spacing: 0.01em;
  position: relative;
  z-index: 1;
}

.user-bubble .message-content {
  color: #FFFFFF;
  /* 适度的文字阴影以提高可读性 */
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.25),
               0 0 1px rgba(0, 0, 0, 0.15);
  font-weight: var(--font-weight-medium);
}

.assistant-bubble .message-content {
  color: var(--text-primary);
}

.assistant-card {
  max-width: 100%;
  margin: 0;
}

.loading-bubble {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md) var(--spacing-lg);
  min-height: 48px;
}

.loading-dots {
  display: flex;
  gap: var(--spacing-xs);
}

.loading-dots span {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  animation: bounce 1.4s ease-in-out infinite;
}

.loading-dots span:nth-child(1) {
  animation-delay: 0s;
}

.loading-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.loading-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1.2);
    opacity: 1;
  }
}

.loading-text {
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  letter-spacing: 0.3px;
}

.input-card {
  background: var(--bg-elevated) !important;
  border: var(--border-width-thin) solid var(--border-color-light) !important;
  border-radius: var(--radius-2xl) !important;
  box-shadow: var(--shadow-warm-md) !important;
  backdrop-filter: blur(20px);
  flex-shrink: 0;
  transition: all var(--transition-base);
  outline: none !important;
}

.input-card :deep(.n-card) {
  outline: none !important;
  border: none !important;
}

.input-card :deep(.n-card__content) {
  outline: none !important;
  padding: var(--spacing-md) !important;
}

.experience-mode-selector {
  margin-bottom: var(--spacing-lg);
  padding-bottom: var(--spacing-lg);
  border-bottom: var(--border-width-thin) solid var(--border-color-light);
}

.mode-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-md);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.mode-buttons {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.mode-button {
  flex: 1;
  min-width: 100px;
  border-radius: var(--radius-lg);
  transition: all var(--transition-base);
}

.mode-button:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-warm-sm);
}

.risk-warning {
  margin-bottom: var(--spacing-md);
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.input-card:hover {
  box-shadow: var(--shadow-warm-lg) !important;
}

.input-wrapper {
  display: flex;
  gap: var(--spacing-lg);
  align-items: flex-end;
  padding: var(--spacing-sm) 0;
}

.chat-input {
  flex: 1;
}

/* 移除所有可能的绿色边框和焦点样式 */
.chat-input :deep(.n-input) {
  outline: none !important;
  border: none !important;
  border-color: transparent !important;
}

.chat-input :deep(.n-input:focus) {
  outline: none !important;
  box-shadow: none !important;
  border: none !important;
  border-color: transparent !important;
}

.chat-input :deep(.n-input:focus-within) {
  outline: none !important;
  border: none !important;
  border-color: transparent !important;
}

.chat-input :deep(.n-input-wrapper) {
  outline: none !important;
  border: none !important;
  border-color: transparent !important;
  padding: 0 !important;
  margin: 0 !important;
}

.chat-input :deep(.n-input-wrapper:focus-within) {
  outline: none !important;
  border: none !important;
  border-color: transparent !important;
  box-shadow: none !important;
  padding: 0 !important;
  margin: 0 !important;
}

.chat-input :deep(.n-input-wrapper:focus) {
  outline: none !important;
  border: none !important;
  border-color: transparent !important;
  box-shadow: none !important;
  padding: 0 !important;
  margin: 0 !important;
}

.chat-input :deep(.n-input__border) {
  border: none !important;
  border-color: transparent !important;
  outline: none !important;
}

.chat-input :deep(.n-input__state-border) {
  border: none !important;
  border-color: transparent !important;
  outline: none !important;
}

.chat-input :deep(.n-input__border--focus) {
  border: none !important;
  border-color: transparent !important;
  outline: none !important;
}

.chat-input :deep(.n-input__border--active) {
  border: none !important;
  border-color: transparent !important;
  outline: none !important;
}

/* 覆盖聚焦状态的所有边框 */
.chat-input :deep(.n-input-wrapper--focus),
.chat-input :deep(.n-input-wrapper--focus *),
.chat-input :deep(.n-input--focus),
.chat-input :deep(.n-input--focus *),
.chat-input :deep(.n-input-wrapper--focus .n-input__border),
.chat-input :deep(.n-input-wrapper--focus .n-input__state-border),
.chat-input :deep(.n-input-wrapper--focus .n-input__border--focus) {
  border: none !important;
  border-color: transparent !important;
  outline: none !important;
}

/* 覆盖包装元素的边框颜色，但不影响 textarea 本身 */
.chat-input :deep(.n-input-wrapper > *) {
  border-color: transparent !important;
}

.chat-input :deep(.n-input-wrapper > *:not(.n-input__textarea-el)) {
  border-color: transparent !important;
}

/* 强制覆盖所有包装器状态下的边框 */
.chat-input :deep(.n-input-wrapper),
.chat-input :deep(.n-input-wrapper *:not(.n-input__textarea-el)) {
  border-color: transparent !important;
}

.chat-input :deep(.n-input__textarea-el) {
  font-size: var(--font-size-base);
  line-height: 1.7;
  color: var(--text-primary);
  border-radius: var(--radius-xl);
  border: var(--border-width-thin) solid var(--border-color-base) !important;
  border-color: var(--border-color-base) !important;
  transition: all var(--transition-base);
  padding: var(--spacing-md) var(--spacing-lg) !important;
  background: var(--bg-elevated);
  resize: none;
  outline: none !important;
  box-sizing: border-box !important;
  width: 100% !important;
  margin: 0 !important;
  vertical-align: top !important;
  letter-spacing: 0.01em;
}

/* 强制覆盖所有可能的绿色边框（包括验证状态） */
.chat-input :deep(.n-input--success),
.chat-input :deep(.n-input--success *),
.chat-input :deep(.n-input-wrapper--success),
.chat-input :deep(.n-input-wrapper--success *) {
  border-color: transparent !important;
}

.chat-input :deep(.n-input__border--success) {
  border: none !important;
  border-color: transparent !important;
  display: none !important;
}

/* 覆盖所有可能的边框元素（包括聚焦时的绿色边框） */
.chat-input :deep(.n-input__border),
.chat-input :deep(.n-input__state-border),
.chat-input :deep(.n-input__border--focus),
.chat-input :deep(.n-input__border--active),
.chat-input :deep(.n-input__border--hover) {
  border: none !important;
  border-color: transparent !important;
  box-shadow: none !important;
  display: none !important;
}

/* 覆盖聚焦时的包装器边框 */
.chat-input :deep(.n-input-wrapper--focus .n-input__border),
.chat-input :deep(.n-input-wrapper--focus .n-input__state-border) {
  border: none !important;
  border-color: transparent !important;
  box-shadow: none !important;
  display: none !important;
}

/* 覆盖所有可能的绿色 box-shadow（Naive UI 可能使用 box-shadow 作为边框） */
/* 但不影响 textarea 本身 */
.chat-input :deep(.n-input-wrapper),
.chat-input :deep(.n-input-wrapper *:not(.n-input__textarea-el)),
.chat-input :deep(.n-input),
.chat-input :deep(.n-input *:not(.n-input__textarea-el)) {
  box-shadow: none !important;
}

/* 覆盖聚焦时的 box-shadow（但不影响 textarea） */
.chat-input :deep(.n-input-wrapper--focus),
.chat-input :deep(.n-input-wrapper--focus *:not(.n-input__textarea-el)) {
  box-shadow: none !important;
}

/* 覆盖所有可能的伪元素边框 */
.chat-input :deep(.n-input-wrapper::before),
.chat-input :deep(.n-input-wrapper::after),
.chat-input :deep(.n-input-wrapper--focus::before),
.chat-input :deep(.n-input-wrapper--focus::after),
.chat-input :deep(.n-input__border::before),
.chat-input :deep(.n-input__border::after),
.chat-input :deep(.n-input__state-border::before),
.chat-input :deep(.n-input__state-border::after) {
  border: none !important;
  border-color: transparent !important;
  box-shadow: none !important;
  display: none !important;
}

/* 覆盖按钮的验证状态边框 */
.send-button :deep(.n-button--success),
.send-button :deep(.n-button--success *),
.send-button :deep(.n-button__border--success) {
  border: none !important;
  border-color: transparent !important;
  display: none !important;
}

.chat-input :deep(.n-input__textarea-el:focus) {
  border-color: var(--color-primary) !important;
  box-shadow: 0 0 0 3px var(--color-primary-lighter) !important;
  background: var(--bg-elevated);
  outline: none !important;
}

.chat-input :deep(.n-input__textarea-el:focus-visible) {
  outline: none !important;
  border-color: var(--color-primary) !important;
  box-shadow: 0 0 0 4px var(--color-primary-lighter) !important;
}

.chat-input :deep(.n-input__textarea-el::placeholder) {
  color: var(--text-disabled);
  opacity: 1;
  line-height: var(--line-height-relaxed);
}

.send-button {
  height: auto;
  padding: var(--spacing-md) var(--spacing-xl);
  border-radius: var(--radius-xl);
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%) !important;
  border: none !important;
  border-color: transparent !important;
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-base);
  box-shadow: var(--shadow-warm-md);
  transition: all var(--transition-base);
  white-space: nowrap;
  outline: none !important;
  letter-spacing: 0.3px;
}

/* 覆盖所有可能的边框颜色 */
.send-button :deep(*) {
  border-color: transparent !important;
}

.send-button :deep(button) {
  outline: none !important;
  border: none !important;
  border-color: transparent !important;
}

.send-button :deep(.n-button__border),
.send-button :deep(.n-button__state-border),
.send-button :deep(.n-button__border--focus),
.send-button :deep(.n-button__border--hover) {
  border: none !important;
  border-color: transparent !important;
  display: none !important;
}

.send-button :deep(button:focus) {
  outline: none !important;
  box-shadow: 0 4px 18px rgba(255, 182, 193, 0.35) !important;
}

.send-button :deep(button:focus-visible) {
  outline: none !important;
  box-shadow: 0 4px 18px rgba(255, 182, 193, 0.35) !important;
}

.send-button :deep(button:active) {
  outline: none !important;
}

.send-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-warm-lg);
}

.send-button:active:not(:disabled) {
  transform: translateY(-1px) scale(0.98);
}

.send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
}

.send-button:focus,
.send-button:focus-visible {
  outline: none !important;
  box-shadow: 0 4px 18px rgba(255, 182, 193, 0.35) !important;
}

.send-icon {
  font-size: 18px;
  margin-right: 4px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chat-layout {
    height: calc(100vh - 160px);
  }

  .sidebar {
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 100;
    transform: translateX(0);
    transition: transform 0.3s ease;
  }

  .sidebar-collapsed {
    transform: translateX(-100%);
  }

  .chat-container {
    width: 100%;
    gap: 1rem;
  }
  
  .emotion-card-content {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }
  
  .emotion-left {
    width: 100%;
  }
  
  .message-bubble {
    max-width: 85%;
    padding: var(--spacing-md) var(--spacing-lg);
  }
  
  .user-message {
    padding-left: var(--spacing-md);
  }
  
  .assistant-message {
    padding-right: var(--spacing-md);
  }
  
  .input-wrapper {
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .send-button {
    width: 100%;
    padding: 12px 20px;
  }
}

@media (max-width: 480px) {
  .emotion-icon-wrapper {
    width: 40px;
    height: 40px;
  }
  
  .emotion-icon {
    font-size: 24px;
  }
  
  .message-bubble {
    max-width: 90%;
    padding: var(--spacing-sm) var(--spacing-md);
    font-size: 14px;
  }
  
  .user-message {
    padding-left: var(--spacing-sm);
  }
  
  .assistant-message {
    padding-right: var(--spacing-sm);
  }
  
  .messages-container {
    padding: var(--spacing-md) var(--spacing-sm);
    gap: var(--spacing-md);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>

