<template>
  <div class="flex flex-col" style="height: calc(100vh - 200px)">
    <!-- 顶部：今日主情绪 -->
    <n-card class="mb-4">
      <div class="flex items-center justify-between">
        <span class="text-sm text-gray-600">{{ $t('chat.todayEmotion') }}</span>
        <span class="text-lg font-medium text-gray-900">
          {{ todayEmotion ? getEmotionLabel(todayEmotion) : $t('chat.noEmotion') }}
        </span>
      </div>
    </n-card>

    <!-- 聊天记录区域 -->
    <div class="flex-1 overflow-y-auto mb-4 space-y-4">
      <div v-if="messages.length === 0" class="text-center text-gray-500 py-12">
        <p class="text-lg mb-2">{{ $t('chat.welcome') }}</p>
        <p class="text-sm">{{ $t('chat.welcomeDesc') }}</p>
      </div>

      <div
        v-for="(msg, index) in messages"
        :key="index"
        :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']"
      >
        <div
          :class="[
            'max-w-[70%] rounded-lg px-4 py-2',
            msg.role === 'user'
              ? 'bg-blue-500 text-white'
              : 'bg-white text-gray-900 border border-gray-200',
          ]"
        >
          <p class="whitespace-pre-wrap">{{ msg.content }}</p>
        </div>
      </div>

      <div v-if="loading" class="flex justify-start">
        <div class="bg-white border border-gray-200 rounded-lg px-4 py-2">
          <span class="text-gray-500">{{ $t('chat.sending') }}</span>
        </div>
      </div>

      <div ref="messagesEndRef" />
    </div>

    <!-- 输入区域 -->
    <n-card>
      <div class="flex space-x-2">
        <n-input
          v-model:value="input"
          type="textarea"
          :placeholder="$t('chat.inputPlaceholder')"
          :rows="2"
          :disabled="loading"
          @keydown="handleKeyPress"
          class="flex-1"
        />
        <n-button
          type="primary"
          :loading="loading"
          :disabled="!input.trim()"
          @click="handleSend"
        >
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
.space-y-4 > * + * {
  margin-top: 1rem;
}

.space-x-2 > * + * {
  margin-left: 0.5rem;
}
</style>

