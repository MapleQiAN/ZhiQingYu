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
            <div class="session-preview">{{ session.preview || $t('chat.newChat') }}</div>
            <div class="session-time">
              {{ formatSessionTime(session.latest_message_at || session.created_at) }}
            </div>
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
        <div
          :class="[
            'message-bubble',
            msg.role === 'user' ? 'user-bubble' : 'assistant-bubble',
          ]"
        >
          <p class="message-content">{{ msg.content }}</p>
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
import { ref, nextTick, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { NCard, NInput, NButton, useMessage } from 'naive-ui'
import {
  sendChatMessage,
  getSessions,
  getSessionMessages,
  type ChatMessage,
  type SessionItem,
} from '@/lib/api'

const { t } = useI18n()
const message = useMessage()

const messages = ref<ChatMessage[]>([])
const input = ref('')
const loading = ref(false)
const sessionId = ref<string | null>(null)
const todayEmotion = ref<string | null>(null)
const messagesEndRef = ref<HTMLDivElement | null>(null)
const sidebarCollapsed = ref(false)
const sessions = ref<SessionItem[]>([])
const loadingSessions = ref(false)

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
  input.value = ''
  loading.value = true

  try {
    const response = await sendChatMessage({
      session_id: sessionId.value,
      messages: newMessages,
    })

    if (response.error) {
      console.error('API Error:', response.error)
      message.error(`${t('common.error')}: ${response.error.message}`)
      return
    }

    if (response.data) {
      const data = response.data
      sessionId.value = data.session_id
      todayEmotion.value = data.emotion

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: data.reply,
      }

      messages.value = [...newMessages, assistantMessage]
      scrollToBottom()
      // 刷新会话列表
      loadSessions()
    }
  } catch (error) {
    console.error('Request failed:', error)
    message.error(t('chat.sendFailed'))
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
.chat-layout {
  display: flex;
  height: calc(100vh - 180px);
  min-height: 600px;
  gap: 1rem;
}

.sidebar {
  width: 280px;
  min-width: 280px;
  background: rgba(255, 255, 255, 0.98);
  border: 1px solid rgba(255, 182, 193, 0.25);
  border-radius: 24px;
  box-shadow: 0 4px 24px rgba(255, 182, 193, 0.12);
  backdrop-filter: blur(20px);
  display: flex;
  flex-direction: column;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.sidebar-collapsed {
  width: 60px;
  min-width: 60px;
}

.sidebar-header {
  padding: 1rem;
  display: flex;
  gap: 0.5rem;
  align-items: center;
  border-bottom: 1px solid rgba(255, 182, 193, 0.15);
  flex-shrink: 0;
}

.sidebar-toggle {
  flex-shrink: 0;
}

.new-chat-button {
  flex: 1;
  background: linear-gradient(135deg, #FFB6C1 0%, #FFA07A 100%) !important;
  border: none !important;
  border-color: transparent !important;
  border-radius: 12px !important;
  font-weight: 600;
  transition: all 0.3s ease;
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
  box-shadow: 0 4px 12px rgba(255, 182, 193, 0.35) !important;
}

.new-chat-button:focus,
.new-chat-button:focus-visible {
  outline: none !important;
  box-shadow: 0 4px 12px rgba(255, 182, 193, 0.35) !important;
}

.sidebar-collapsed .new-chat-button {
  display: none;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
}

.sidebar-content::-webkit-scrollbar {
  width: 6px;
}

.sidebar-content::-webkit-scrollbar-track {
  background: rgba(255, 182, 193, 0.05);
  border-radius: 10px;
}

.sidebar-content::-webkit-scrollbar-thumb {
  background: rgba(255, 182, 193, 0.3);
  border-radius: 10px;
}

.sidebar-content::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 182, 193, 0.5);
}

.sidebar-title {
  font-size: 14px;
  font-weight: 600;
  color: #8B6F7E;
  margin-bottom: 1rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sidebar-loading,
.sidebar-empty {
  text-align: center;
  padding: 2rem 1rem;
  color: #A68A8A;
  font-size: 14px;
}

.session-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.session-item {
  padding: 0.75rem 1rem;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid transparent;
  background: rgba(255, 182, 193, 0.05);
}

.session-item:hover {
  background: rgba(255, 182, 193, 0.15);
  transform: translateX(4px);
  border-color: rgba(255, 182, 193, 0.3);
}

.session-item.active {
  background: linear-gradient(135deg, rgba(255, 182, 193, 0.2) 0%, rgba(255, 218, 185, 0.2) 100%);
  border-color: rgba(255, 182, 193, 0.4);
  box-shadow: 0 2px 8px rgba(255, 182, 193, 0.2);
}

.session-preview {
  font-size: 14px;
  color: #4A4A4A;
  margin-bottom: 0.25rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.4;
}

.session-item.active .session-preview {
  color: #8B6F7E;
  font-weight: 500;
}

.session-time {
  font-size: 12px;
  color: #A68A8A;
}

.session-item.active .session-time {
  color: #8B6F7E;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  min-width: 0;
}

.emotion-card {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(255, 250, 245, 0.98) 100%) !important;
  border: 1px solid rgba(255, 182, 193, 0.25) !important;
  border-radius: 24px !important;
  box-shadow: 0 4px 24px rgba(255, 182, 193, 0.12) !important;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
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
  box-shadow: 0 8px 40px rgba(255, 182, 193, 0.2) !important;
  transform: translateY(-3px);
  border-color: rgba(255, 182, 193, 0.35) !important;
}

.emotion-card-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0;
}

.emotion-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.emotion-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, rgba(255, 182, 193, 0.15) 0%, rgba(255, 218, 185, 0.15) 100%);
  border-radius: 16px;
  border: 1px solid rgba(255, 182, 193, 0.2);
}

.emotion-icon {
  font-size: 28px;
  filter: drop-shadow(0 2px 6px rgba(255, 182, 193, 0.4));
  animation: float 3s ease-in-out infinite;
}

.emotion-label {
  font-size: 1rem;
  font-weight: 600;
  color: #8B6F7E;
  letter-spacing: 0.3px;
}

.emotion-badge {
  padding: 10px 24px;
  background: linear-gradient(135deg, rgba(255, 182, 193, 0.2) 0%, rgba(255, 218, 185, 0.2) 100%);
  border-radius: 20px;
  border: 1px solid rgba(255, 182, 193, 0.35);
  box-shadow: 0 2px 8px rgba(255, 182, 193, 0.15);
  transition: all 0.3s ease;
}

.emotion-badge:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(255, 182, 193, 0.25);
}

.emotion-text {
  font-size: 16px;
  font-weight: 600;
  background: linear-gradient(135deg, #D9779F 0%, #C97A9A 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 0.5rem;
  scroll-behavior: smooth;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-height: 0;
}

.messages-container::-webkit-scrollbar {
  width: 8px;
}

.messages-container::-webkit-scrollbar-track {
  background: rgba(255, 182, 193, 0.05);
  border-radius: 10px;
}

.messages-container::-webkit-scrollbar-thumb {
  background: rgba(255, 182, 193, 0.3);
  border-radius: 10px;
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 182, 193, 0.5);
}

.welcome-section {
  text-align: center;
  padding: 60px 20px;
  animation: fadeIn 0.6s ease;
}

.welcome-icon {
  font-size: 64px;
  margin-bottom: 20px;
  filter: drop-shadow(0 4px 8px rgba(255, 182, 193, 0.3));
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}

.welcome-title {
  font-size: 24px;
  font-weight: 600;
  color: #8B6F7E;
  margin-bottom: 12px;
  background: linear-gradient(135deg, #D9779F 0%, #C97A9A 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.welcome-desc {
  font-size: 15px;
  color: #A68A8A;
  line-height: 1.6;
}

.message-wrapper {
  display: flex;
  animation: slideIn 0.3s ease;
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
}

.assistant-message {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 75%;
  padding: 16px 20px;
  border-radius: 22px;
  word-wrap: break-word;
  position: relative;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  line-height: 1.6;
}

.message-bubble:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.12);
}

.user-bubble {
  background: linear-gradient(135deg, #FFB6C1 0%, #FFA07A 100%);
  color: white;
  border-bottom-right-radius: 8px;
  box-shadow: 0 4px 16px rgba(255, 182, 193, 0.3);
}

.assistant-bubble {
  background: rgba(255, 255, 255, 0.98);
  color: #4A4A4A;
  border: 1px solid rgba(255, 182, 193, 0.25);
  border-bottom-left-radius: 8px;
  backdrop-filter: blur(15px);
  box-shadow: 0 4px 16px rgba(255, 182, 193, 0.1);
}

.message-content {
  margin: 0;
  line-height: 1.6;
  font-size: 15px;
  white-space: pre-wrap;
}

.loading-bubble {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 18px;
}

.loading-dots {
  display: flex;
  gap: 4px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(255, 182, 193, 0.6);
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
  color: #A68A8A;
  font-size: 14px;
}

.input-card {
  background: rgba(255, 255, 255, 0.98) !important;
  border: 1px solid rgba(255, 182, 193, 0.25) !important;
  border-radius: 24px !important;
  box-shadow: 0 4px 24px rgba(255, 182, 193, 0.12) !important;
  backdrop-filter: blur(20px);
  flex-shrink: 0;
  transition: all 0.3s ease;
  outline: none !important;
}

.input-card :deep(.n-card) {
  outline: none !important;
  border: none !important;
}

.input-card :deep(.n-card__content) {
  outline: none !important;
}

.input-card:hover {
  box-shadow: 0 6px 32px rgba(255, 182, 193, 0.18) !important;
}

.input-wrapper {
  display: flex;
  gap: 1rem;
  align-items: flex-end;
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
  font-size: 15px;
  line-height: 1.7;
  color: #4A4A4A;
  border-radius: 18px;
  border: 1px solid rgba(255, 182, 193, 0.3) !important;
  border-color: rgba(255, 182, 193, 0.3) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 14px 18px !important;
  background: rgba(255, 255, 255, 0.8);
  resize: none;
  outline: none !important;
  box-sizing: border-box !important;
  width: 100% !important;
  margin: 0 !important;
  vertical-align: top !important;
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
  border-color: rgba(255, 182, 193, 0.6) !important;
  box-shadow: 0 0 0 4px rgba(255, 182, 193, 0.12) !important;
  background: rgba(255, 255, 255, 1);
  outline: none !important;
}

.chat-input :deep(.n-input__textarea-el:focus-visible) {
  outline: none !important;
  border-color: rgba(255, 182, 193, 0.6) !important;
  box-shadow: 0 0 0 4px rgba(255, 182, 193, 0.12) !important;
}

.chat-input :deep(.n-input__textarea-el::placeholder) {
  color: #B8A8A8;
  opacity: 1;
  line-height: 1.7;
}

.send-button {
  height: auto;
  padding: 14px 28px;
  border-radius: 18px;
  background: linear-gradient(135deg, #FFB6C1 0%, #FFA07A 100%) !important;
  border: none !important;
  border-color: transparent !important;
  font-weight: 600;
  font-size: 15px;
  box-shadow: 0 4px 18px rgba(255, 182, 193, 0.35);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
  outline: none !important;
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
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 8px 28px rgba(255, 182, 193, 0.45);
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
    padding: 14px 18px;
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
    padding: 12px 16px;
    font-size: 14px;
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

