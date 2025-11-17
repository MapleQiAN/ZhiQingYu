<template>
  <div class="heart-card">
    <!-- 卡片装饰性顶部 -->
    <div class="card-header">
      <div class="card-icon">💝</div>
      <div class="card-title" v-if="cardData.theme">{{ cardData.theme }}</div>
      <div class="card-title-placeholder" v-else>{{ $t('chat.cardTitle') }}</div>
    </div>

    <!-- 卡片内容区域 -->
    <div class="card-content">
      <!-- 情感回音板块 -->
      <div v-if="cardData.emotion_echo" class="card-section emotion-section">
        <div class="section-header">
          <span class="section-icon">💭</span>
          <span class="section-title">{{ $t('chat.emotionEcho') }}</span>
        </div>
        <div class="section-content">{{ cardData.emotion_echo }}</div>
      </div>

      <!-- 认知澄清板块 -->
      <div v-if="cardData.clarification" class="card-section clarification-section">
        <div class="section-header">
          <span class="section-icon">🔍</span>
          <span class="section-title">{{ $t('chat.clarification') }}</span>
        </div>
        <div class="section-content">{{ cardData.clarification }}</div>
      </div>

      <!-- 建议板块 -->
      <div v-if="hasSuggestions" class="card-section suggestion-section">
        <div class="section-header">
          <span class="section-icon">✨</span>
          <span class="section-title">{{ $t('chat.suggestion') }}</span>
        </div>
        <div class="section-content">
          <ul v-if="Array.isArray(cardData.suggestion)" class="suggestion-list">
            <li v-for="(item, index) in cardData.suggestion" :key="index" class="suggestion-item">
              {{ item }}
            </li>
          </ul>
          <div v-else class="suggestion-text">{{ cardData.suggestion }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { CardData } from '@/lib/api'

interface Props {
  cardData: CardData
}

const props = defineProps<Props>()

const hasSuggestions = computed(() => {
  if (!props.cardData.suggestion) return false
  if (Array.isArray(props.cardData.suggestion)) {
    return props.cardData.suggestion.length > 0
  }
  return props.cardData.suggestion.trim().length > 0
})
</script>

<style scoped>
.heart-card {
  background: linear-gradient(135deg, 
    rgba(255, 250, 245, 0.95) 0%, 
    rgba(255, 240, 240, 0.95) 50%,
    rgba(255, 250, 245, 0.95) 100%);
  border-radius: var(--radius-2xl);
  padding: var(--spacing-xl);
  box-shadow: 
    0 4px 20px rgba(232, 180, 184, 0.15),
    0 2px 8px rgba(232, 180, 184, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(232, 180, 184, 0.2);
  position: relative;
  overflow: hidden;
  backdrop-filter: blur(10px);
}

.heart-card::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(
    circle,
    rgba(255, 200, 200, 0.1) 0%,
    transparent 70%
  );
  pointer-events: none;
}

.card-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-xl);
  padding-bottom: var(--spacing-lg);
  border-bottom: 2px solid rgba(232, 180, 184, 0.2);
  position: relative;
  z-index: 1;
}

.card-icon {
  font-size: 2rem;
  line-height: 1;
  animation: gentle-pulse 3s ease-in-out infinite;
}

@keyframes gentle-pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.9;
  }
}

.card-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-primary-dark);
  line-height: 1.4;
}

.card-title-placeholder {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-secondary);
  line-height: 1.4;
}

.card-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
  position: relative;
  z-index: 1;
}

.card-section {
  background: rgba(255, 255, 255, 0.6);
  border-radius: var(--radius-xl);
  padding: var(--spacing-lg);
  border: 1px solid rgba(232, 180, 184, 0.15);
  transition: all var(--transition-base);
  backdrop-filter: blur(5px);
}

.card-section:hover {
  background: rgba(255, 255, 255, 0.8);
  border-color: rgba(232, 180, 184, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(232, 180, 184, 0.15);
}

.section-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.section-icon {
  font-size: 1.25rem;
  line-height: 1;
}

.section-title {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-primary-dark);
  letter-spacing: 0.3px;
}

.section-content {
  font-size: var(--font-size-base);
  line-height: 1.8;
  color: var(--text-primary);
  white-space: pre-wrap;
  word-break: break-word;
}

.emotion-section {
  border-left: 3px solid rgba(255, 182, 193, 0.5);
}

.clarification-section {
  border-left: 3px solid rgba(176, 196, 222, 0.5);
}

.suggestion-section {
  border-left: 3px solid rgba(255, 218, 185, 0.5);
}

.suggestion-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.suggestion-item {
  padding-left: var(--spacing-lg);
  position: relative;
  line-height: 1.8;
}

.suggestion-item::before {
  content: '•';
  position: absolute;
  left: 0;
  color: var(--color-primary);
  font-size: 1.5rem;
  line-height: 1;
  top: 0.1em;
}

.suggestion-text {
  line-height: 1.8;
}
</style>

