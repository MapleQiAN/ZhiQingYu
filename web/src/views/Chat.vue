<template>
  <div class="flex flex-col chat-container">
    <!-- 顶部：今日主情绪 -->
    <n-card class="mb-6 emotion-card" hoverable>
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div class="emotion-icon">💭</div>
          <span class="text-sm font-medium text-gray-600">{{ $t('chat.todayEmotion') }}</span>
        </div>
        <div class="emotion-badge">
          <span class="emotion-text">
            {{ todayEmotion ? getEmotionLabel(todayEmotion) : $t('chat.noEmotion') }}
          </span>
        </div>
      </div>
    </n-card>

    <!-- 聊天记录区域 -->
    <div class="flex-1 overflow-y-auto mb-6 space-y-4 messages-container">
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
      <div class="flex space-x-3">
        <n-input
          v-model:value="input"
          type="textarea"
          :placeholder="$t('chat.inputPlaceholder')"
          :rows="3"
          :disabled="loading"
          @keydown="handleKeyPress"
          class="flex-1 chat-input"
          :autosize="{ minRows: 2, maxRows: 5 }"
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
            <span>✨</span>
          </template>
          {{ $t('common.send') }}
        </n-button>
      </div>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { NCard, NInput, NButton, useMessage } from 'naive-ui'
import { sendChatMessage, type ChatMessage, type ChatResponse } from '@/lib/api'

const { t } = useI18n()
const message = useMessage()

const messages = ref<ChatMessage[]>([])
const input = ref('')
const loading = ref(false)
const sessionId = ref<string | null>(null)
const todayEmotion = ref<string | null>(null)
const messagesEndRef = ref<HTMLDivElement | null>(null)

const scrollToBottom = async () => {
  await nextTick()
  messagesEndRef.value?.scrollIntoView({ behavior: 'smooth' })
}

onMounted(() => {
  scrollToBottom()
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
.chat-container {
  height: calc(100vh - 220px);
  min-height: 600px;
}

.emotion-card {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 250, 245, 0.95) 100%) !important;
  border: 1px solid rgba(255, 182, 193, 0.2) !important;
  border-radius: 20px !important;
  box-shadow: 0 4px 20px rgba(255, 182, 193, 0.1) !important;
  transition: all 0.3s ease !important;
}

.emotion-card:hover {
  box-shadow: 0 6px 30px rgba(255, 182, 193, 0.15) !important;
  transform: translateY(-2px);
}

.emotion-icon {
  font-size: 24px;
  filter: drop-shadow(0 2px 4px rgba(255, 182, 193, 0.3));
}

.emotion-badge {
  padding: 8px 20px;
  background: linear-gradient(135deg, rgba(255, 182, 193, 0.15) 0%, rgba(255, 218, 185, 0.15) 100%);
  border-radius: 20px;
  border: 1px solid rgba(255, 182, 193, 0.3);
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
  padding: 8px 4px;
  scroll-behavior: smooth;
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
  max-width: 70%;
  padding: 14px 18px;
  border-radius: 20px;
  word-wrap: break-word;
  position: relative;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.2s ease;
}

.message-bubble:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.user-bubble {
  background: linear-gradient(135deg, #FFB6C1 0%, #FFA07A 100%);
  color: white;
  border-bottom-right-radius: 6px;
}

.assistant-bubble {
  background: rgba(255, 255, 255, 0.95);
  color: #4A4A4A;
  border: 1px solid rgba(255, 182, 193, 0.2);
  border-bottom-left-radius: 6px;
  backdrop-filter: blur(10px);
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
  background: rgba(255, 255, 255, 0.95) !important;
  border: 1px solid rgba(255, 182, 193, 0.2) !important;
  border-radius: 20px !important;
  box-shadow: 0 4px 20px rgba(255, 182, 193, 0.1) !important;
  backdrop-filter: blur(10px);
}

.chat-input :deep(.n-input__textarea-el) {
  font-size: 15px;
  line-height: 1.6;
  color: #4A4A4A;
  border-radius: 16px;
  border: 1px solid rgba(255, 182, 193, 0.3);
  transition: all 0.3s ease;
  padding: 12px 16px;
}

.chat-input :deep(.n-input__textarea-el:focus) {
  border-color: rgba(255, 182, 193, 0.6);
  box-shadow: 0 0 0 3px rgba(255, 182, 193, 0.1);
}

.send-button {
  height: auto;
  padding: 12px 24px;
  border-radius: 16px;
  background: linear-gradient(135deg, #FFB6C1 0%, #FFA07A 100%) !important;
  border: none !important;
  font-weight: 600;
  box-shadow: 0 4px 15px rgba(255, 182, 193, 0.3);
  transition: all 0.3s ease;
}

.send-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 182, 193, 0.4);
}

.send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.space-y-4 > * + * {
  margin-top: 1rem;
}

.space-x-3 > * + * {
  margin-left: 0.75rem;
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

