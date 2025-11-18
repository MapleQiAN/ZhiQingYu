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
      <!-- 5步骤内容展示（优先） -->
      <!-- Step 1: 情绪接住 & 问题确认 -->
      <div v-if="cardData.step1_emotion_mirror || cardData.step1_problem_restate" class="card-section step-section step1-section">
        <div class="section-header">
          <span class="section-icon">💭</span>
          <span class="section-title">{{ $t('chat.step1') }}</span>
        </div>
        <div class="section-content">
          <div v-if="cardData.step1_emotion_mirror" class="step-content-item">
            <div class="step-label">{{ $t('chat.emotionMirror') }}</div>
            <div class="step-text">{{ cardData.step1_emotion_mirror }}</div>
          </div>
          <div v-if="cardData.step1_problem_restate" class="step-content-item">
            <div class="step-label">{{ $t('chat.problemRestate') }}</div>
            <div class="step-text">{{ cardData.step1_problem_restate }}</div>
          </div>
        </div>
      </div>

      <!-- Step 2: 结构化拆解问题 -->
      <div v-if="cardData.step2_breakdown" class="card-section step-section step2-section">
        <div class="section-header">
          <span class="section-icon">🔍</span>
          <span class="section-title">{{ $t('chat.step2') }}</span>
        </div>
        <div class="section-content">{{ cardData.step2_breakdown }}</div>
      </div>

      <!-- Step 3: 专业视角解释 -->
      <div v-if="cardData.step3_explanation" class="card-section step-section step3-section">
        <div class="section-header">
          <span class="section-icon">💡</span>
          <span class="section-title">{{ $t('chat.step3') }}</span>
        </div>
        <div class="section-content">{{ cardData.step3_explanation }}</div>
      </div>

      <!-- Step 4: 小步可执行建议 -->
      <div v-if="hasStep4Suggestions" class="card-section step-section step4-section">
        <div class="section-header">
          <span class="section-icon">✨</span>
          <span class="section-title">{{ $t('chat.step4') }}</span>
        </div>
        <div class="section-content">
          <ul v-if="Array.isArray(cardData.step4_suggestions)" class="suggestion-list">
            <li v-for="(item, index) in cardData.step4_suggestions" :key="index" class="suggestion-item">
              {{ item }}
            </li>
          </ul>
          <div v-else class="suggestion-text">{{ cardData.step4_suggestions }}</div>
        </div>
      </div>

      <!-- Step 5: 温柔收尾 & 小结 -->
      <div v-if="cardData.step5_summary" class="card-section step-section step5-section">
        <div class="section-header">
          <span class="section-icon">🌺</span>
          <span class="section-title">{{ $t('chat.step5') }}</span>
        </div>
        <div class="section-content">{{ cardData.step5_summary }}</div>
      </div>

      <!-- 兼容旧版格式：情感回音板块 -->
      <div v-if="!hasStepContent && cardData.emotion_echo" class="card-section emotion-section">
        <div class="section-header">
          <span class="section-icon">💭</span>
          <span class="section-title">{{ $t('chat.emotionEcho') }}</span>
        </div>
        <div class="section-content">{{ cardData.emotion_echo }}</div>
      </div>

      <!-- 兼容旧版格式：认知澄清板块 -->
      <div v-if="!hasStepContent && cardData.clarification" class="card-section clarification-section">
        <div class="section-header">
          <span class="section-icon">🔍</span>
          <span class="section-title">{{ $t('chat.clarification') }}</span>
        </div>
        <div class="section-content">{{ cardData.clarification }}</div>
      </div>

      <!-- 兼容旧版格式：建议板块 -->
      <div v-if="!hasStepContent && hasSuggestions" class="card-section suggestion-section">
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

const hasStep4Suggestions = computed(() => {
  if (!props.cardData.step4_suggestions) return false
  if (Array.isArray(props.cardData.step4_suggestions)) {
    return props.cardData.step4_suggestions.length > 0
  }
  return props.cardData.step4_suggestions.trim().length > 0
})

const hasStepContent = computed(() => {
  return !!(
    props.cardData.step1_emotion_mirror ||
    props.cardData.step1_problem_restate ||
    props.cardData.step2_breakdown ||
    props.cardData.step3_explanation ||
    props.cardData.step4_suggestions ||
    props.cardData.step5_summary
  )
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

.step-section {
  position: relative;
}

.step1-section {
  border-left: 3px solid rgba(255, 182, 193, 0.6);
}

.step2-section {
  border-left: 3px solid rgba(176, 196, 222, 0.6);
}

.step3-section {
  border-left: 3px solid rgba(255, 218, 185, 0.6);
}

.step4-section {
  border-left: 3px solid rgba(144, 238, 144, 0.6);
}

.step5-section {
  border-left: 3px solid rgba(221, 160, 221, 0.6);
}

.step-content-item {
  margin-bottom: var(--spacing-md);
}

.step-content-item:last-child {
  margin-bottom: 0;
}

.step-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-primary-dark);
  margin-bottom: var(--spacing-xs);
  opacity: 0.8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.step-text {
  line-height: 1.8;
  color: var(--text-primary);
}
</style>

