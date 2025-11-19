import type { CardData } from './api'
import { renderMarkdown } from './markdown'

export type CardTemplate = 'basic' | 'starry' | 'ocean' | 'ancient' | 'sci-fi' | 'candy'

const formatDate = () => {
  return new Date().toLocaleString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const hasStepContent = (cardData: CardData) => {
  return Boolean(
    cardData.step1_emotion_mirror ||
      cardData.step1_problem_restate ||
      cardData.step2_breakdown ||
      cardData.step3_explanation ||
      cardData.step4_suggestions ||
      cardData.step5_summary
  )
}

const shouldUseThreePart = (cardData: CardData) => {
  if (cardData.useThreePart !== undefined) {
    return cardData.useThreePart
  }
  if (hasStepContent(cardData)) {
    return false
  }
  return true
}

const renderArrayOrString = (value?: string[] | string | null) => {
  if (!value) return ''
  if (Array.isArray(value)) {
    const items = value
      .map(item => item?.trim())
      .filter((item): item is string => Boolean(item))
      .map(item => `<li>${renderMarkdown(item)}</li>`)
      .join('')
    return items ? `<ul class="card-list">${items}</ul>` : ''
  }
  return renderMarkdown(value)
}

const renderDoubleColumn = (left?: string | null, right?: string | null) => {
  if (!left && !right) return ''
  return `
    <div class="card-two-column">
      ${
        left
          ? `<div class="card-two-column__item">
              <div class="card-label">情绪镜像</div>
              <div class="card-markdown">${renderMarkdown(left)}</div>
            </div>`
          : ''
      }
      ${
        right
          ? `<div class="card-two-column__item">
              <div class="card-label">问题复述</div>
              <div class="card-markdown">${renderMarkdown(right)}</div>
            </div>`
          : ''
      }
    </div>
  `
}

const buildSection = (options: {
  icon: string
  title: string
  accent: string
  content: string
}) => {
  if (!options.content.trim()) return ''
  return `
    <section class="card-section" style="--section-accent: ${options.accent}">
      <div class="section-header">
        <span class="section-icon">${options.icon}</span>
        <span class="section-title">${options.title}</span>
      </div>
      <div class="section-content">
        ${options.content}
      </div>
    </section>
  `
}

const buildThreePartSections = (cardData: CardData) => {
  const sections = [
    buildSection({
      icon: '💭',
      title: '情感回音',
      accent: '#FFB6C1',
      content: cardData.emotion_echo ? renderMarkdown(cardData.emotion_echo) : '',
    }),
    buildSection({
      icon: '🔍',
      title: '认知澄清',
      accent: '#B0C4DE',
      content: cardData.clarification ? renderMarkdown(cardData.clarification) : '',
    }),
    buildSection({
      icon: '✨',
      title: '暖心建议',
      accent: '#FFDAB9',
      content: renderArrayOrString(cardData.suggestion),
    }),
  ]
  return sections.join('')
}

const buildFiveStepSections = (cardData: CardData) => {
  const sections = [
    buildSection({
      icon: '💭',
      title: '我听见了你的心声',
      accent: '#FFB6C1',
      content: renderDoubleColumn(cardData.step1_emotion_mirror, cardData.step1_problem_restate),
    }),
    buildSection({
      icon: '🔍',
      title: '一起剖析问题吧',
      accent: '#B0C4DE',
      content: cardData.step2_breakdown ? renderMarkdown(cardData.step2_breakdown) : '',
    }),
    buildSection({
      icon: '💡',
      title: ' 或许可以专业一些',
      accent: '#FFDAB9',
      content: cardData.step3_explanation ? renderMarkdown(cardData.step3_explanation) : '',
    }),
    buildSection({
      icon: '🌱',
      title: '小步可执行建议',
      accent: '#90EE90',
      content: renderArrayOrString(cardData.step4_suggestions),
    }),
    buildSection({
      icon: '🌺',
      title: '希望给你一个温柔的收尾',
      accent: '#DDA0DD',
      content: cardData.step5_summary ? renderMarkdown(cardData.step5_summary) : '',
    }),
  ]
  return sections.join('')
}

// 模板样式定义
const getTemplateStyles = (template: CardTemplate): string => {
  const templates: Record<CardTemplate, string> = {
    basic: `
      :root {
        font-size: 16px;
        color-scheme: light;
      }
      * {
        box-sizing: border-box;
      }
      body {
        margin: 0;
        padding: 0;
        font-family: 'Source Han Serif SC', 'Noto Serif SC', 'Segoe UI', 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif;
        background: linear-gradient(120deg, #fffaf5, #ffeef0);
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 48px 24px;
      }
      .card-wrapper {
        width: min(860px, 100%);
        background: rgba(255, 255, 255, 0.95);
        border-radius: 28px;
        padding: 48px;
        box-shadow:
          0 24px 80px rgba(232, 180, 184, 0.2),
          0 12px 30px rgba(232, 180, 184, 0.1),
          inset 0 2px 0 rgba(255, 255, 255, 0.8);
        border: 1px solid rgba(232, 180, 184, 0.3);
        position: relative;
        overflow: hidden;
      }
      .card-wrapper::before,
      .card-wrapper::after {
        content: '';
        position: absolute;
        width: 320px;
        height: 320px;
        background: radial-gradient(circle, rgba(255, 200, 200, 0.25), transparent 70%);
        filter: blur(4px);
        opacity: 0.7;
      }
      .card-wrapper::before {
        top: -160px;
        right: -80px;
      }
      .card-wrapper::after {
        bottom: -120px;
        left: -60px;
        background: radial-gradient(circle, rgba(200, 220, 255, 0.25), transparent 70%);
      }
      .card-theme {
        font-size: 2rem;
        font-weight: 600;
        color: #c2556b;
        letter-spacing: 1px;
        margin-bottom: 12px;
      }
      .card-tagline {
        font-size: 1rem;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        color: rgba(194, 85, 107, 0.6);
        margin-bottom: 20px;
      }
      .card-question {
        font-size: 1.05rem;
        line-height: 1.7;
        color: rgba(0, 0, 0, 0.75);
        margin-top: 20px;
        padding: 16px 20px;
        background: rgba(255, 255, 255, 0.6);
        border-radius: 16px;
        border-left: 3px solid rgba(194, 85, 107, 0.5);
        font-style: italic;
      }
      .card-section {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 22px;
        padding: 24px 28px;
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.6);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.05);
        border-left: 4px solid var(--section-accent, rgba(232, 180, 184, 0.8));
      }
      .card-list li::before {
        content: '✦';
        position: absolute;
        left: 0;
        color: rgba(194, 85, 107, 0.6);
      }
      .card-footer span {
        display: inline-block;
        padding: 8px 18px;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.8);
        border: 1px solid rgba(232, 180, 184, 0.4);
      }
      .card-markdown a,
      .section-content a {
        color: #c2556b;
        text-decoration: none;
        border-bottom: 1px solid rgba(194, 85, 107, 0.4);
      }
    `,
    starry: `
      :root {
        font-size: 16px;
        color-scheme: dark;
      }
      * {
        box-sizing: border-box;
      }
      body {
        margin: 0;
        padding: 0;
        font-family: 'Source Han Serif SC', 'Noto Serif SC', 'Segoe UI', 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif;
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #2d1b4e 100%);
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 48px 24px;
        position: relative;
        overflow: hidden;
      }
      body::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
          radial-gradient(2px 2px at 20% 30%, white, transparent),
          radial-gradient(2px 2px at 60% 70%, white, transparent),
          radial-gradient(1px 1px at 50% 50%, white, transparent),
          radial-gradient(1px 1px at 80% 10%, white, transparent),
          radial-gradient(2px 2px at 90% 40%, white, transparent),
          radial-gradient(1px 1px at 33% 60%, white, transparent),
          radial-gradient(1px 1px at 55% 80%, white, transparent);
        background-size: 200% 200%;
        background-position: 0% 0%;
        animation: starMove 20s linear infinite;
        opacity: 0.6;
        pointer-events: none;
      }
      @keyframes starMove {
        0% { background-position: 0% 0%; }
        100% { background-position: 100% 100%; }
      }
      .card-wrapper {
        width: min(860px, 100%);
        background: rgba(15, 20, 40, 0.85);
        border-radius: 28px;
        padding: 48px;
        box-shadow:
          0 24px 80px rgba(100, 150, 255, 0.3),
          0 12px 30px rgba(100, 150, 255, 0.15),
          inset 0 2px 0 rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(150, 180, 255, 0.3);
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(10px);
      }
      .card-wrapper::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(100, 150, 255, 0.1) 0%, transparent 70%);
        animation: rotate 30s linear infinite;
      }
      @keyframes rotate {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
      .card-theme {
        font-size: 2rem;
        font-weight: 600;
        color: #9bb5ff;
        letter-spacing: 1px;
        margin-bottom: 12px;
        text-shadow: 0 0 20px rgba(155, 181, 255, 0.5);
      }
      .card-tagline {
        font-size: 1rem;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        color: rgba(155, 181, 255, 0.7);
        margin-bottom: 20px;
      }
      .card-question {
        font-size: 1.05rem;
        line-height: 1.7;
        color: rgba(255, 255, 255, 0.85);
        margin-top: 20px;
        padding: 16px 20px;
        background: rgba(100, 150, 255, 0.15);
        border-radius: 16px;
        border-left: 3px solid rgba(155, 181, 255, 0.6);
        font-style: italic;
      }
      .card-section {
        background: rgba(20, 30, 50, 0.7);
        border-radius: 22px;
        padding: 24px 28px;
        margin-bottom: 20px;
        border: 1px solid rgba(150, 180, 255, 0.2);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.3);
        border-left: 4px solid var(--section-accent, rgba(155, 181, 255, 0.6));
      }
      .section-title {
        color: rgba(255, 255, 255, 0.9);
      }
      .section-content {
        color: rgba(255, 255, 255, 0.8);
      }
      .card-date {
        color: rgba(255, 255, 255, 0.5);
      }
      .card-label {
        color: rgba(255, 255, 255, 0.5);
      }
      .card-list li::before {
        content: '⭐';
        position: absolute;
        left: 0;
        color: rgba(155, 181, 255, 0.7);
      }
      .card-footer span {
        display: inline-block;
        padding: 8px 18px;
        border-radius: 999px;
        background: rgba(100, 150, 255, 0.2);
        border: 1px solid rgba(155, 181, 255, 0.4);
        color: rgba(255, 255, 255, 0.7);
      }
      .card-markdown a,
      .section-content a {
        color: #9bb5ff;
        text-decoration: none;
        border-bottom: 1px solid rgba(155, 181, 255, 0.5);
      }
    `,
    ocean: `
      :root {
        font-size: 16px;
        color-scheme: light;
      }
      * {
        box-sizing: border-box;
      }
      body {
        margin: 0;
        padding: 0;
        font-family: 'Source Han Serif SC', 'Noto Serif SC', 'Segoe UI', 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif;
        background: linear-gradient(135deg, #e0f2fe 0%, #b3e5fc 30%, #81d4fa 60%, #4fc3f7 100%);
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 48px 24px;
        position: relative;
        overflow: hidden;
      }
      body::before {
        content: '';
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 40%;
        background: linear-gradient(to top, rgba(33, 150, 243, 0.3), transparent);
        animation: wave 8s ease-in-out infinite;
      }
      @keyframes wave {
        0%, 100% { transform: translateY(0) scaleY(1); }
        50% { transform: translateY(-10px) scaleY(1.1); }
      }
      .card-wrapper {
        width: min(860px, 100%);
        background: rgba(255, 255, 255, 0.95);
        border-radius: 28px;
        padding: 48px;
        box-shadow:
          0 24px 80px rgba(33, 150, 243, 0.25),
          0 12px 30px rgba(33, 150, 243, 0.15),
          inset 0 2px 0 rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(100, 181, 246, 0.4);
        position: relative;
        overflow: hidden;
      }
      .card-wrapper::before {
        content: '';
        position: absolute;
        top: -100px;
        right: -100px;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(100, 181, 246, 0.3), transparent 70%);
        filter: blur(40px);
      }
      .card-wrapper::after {
        content: '';
        position: absolute;
        bottom: -80px;
        left: -80px;
        width: 250px;
        height: 250px;
        background: radial-gradient(circle, rgba(77, 208, 225, 0.3), transparent 70%);
        filter: blur(40px);
      }
      .card-theme {
        font-size: 2rem;
        font-weight: 600;
        color: #0277bd;
        letter-spacing: 1px;
        margin-bottom: 12px;
      }
      .card-tagline {
        font-size: 1rem;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        color: rgba(2, 119, 189, 0.7);
        margin-bottom: 20px;
      }
      .card-question {
        font-size: 1.05rem;
        line-height: 1.7;
        color: rgba(0, 0, 0, 0.75);
        margin-top: 20px;
        padding: 16px 20px;
        background: rgba(227, 242, 253, 0.8);
        border-radius: 16px;
        border-left: 3px solid rgba(33, 150, 243, 0.6);
        font-style: italic;
      }
      .card-section {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 22px;
        padding: 24px 28px;
        margin-bottom: 20px;
        border: 1px solid rgba(187, 222, 251, 0.6);
        box-shadow: 0 12px 30px rgba(33, 150, 243, 0.1);
        border-left: 4px solid var(--section-accent, rgba(33, 150, 243, 0.7));
      }
      .card-list li::before {
        content: '🌊';
        position: absolute;
        left: 0;
        color: rgba(33, 150, 243, 0.7);
      }
      .card-footer span {
        display: inline-block;
        padding: 8px 18px;
        border-radius: 999px;
        background: rgba(227, 242, 253, 0.9);
        border: 1px solid rgba(100, 181, 246, 0.5);
      }
      .card-markdown a,
      .section-content a {
        color: #0277bd;
        text-decoration: none;
        border-bottom: 1px solid rgba(33, 150, 243, 0.5);
      }
    `,
    ancient: `
      :root {
        font-size: 16px;
        color-scheme: light;
      }
      * {
        box-sizing: border-box;
      }
      body {
        margin: 0;
        padding: 0;
        font-family: 'KaiTi', 'STKaiti', 'Source Han Serif SC', 'Noto Serif SC', 'Microsoft YaHei', serif;
        background: linear-gradient(135deg, #f5e6d3 0%, #e8d5c4 50%, #d4c4b0 100%);
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 48px 24px;
        position: relative;
      }
      body::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
          repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(139, 69, 19, 0.03) 2px, rgba(139, 69, 19, 0.03) 4px);
        pointer-events: none;
      }
      .card-wrapper {
        width: min(860px, 100%);
        background: linear-gradient(135deg, #faf8f3 0%, #f5f0e8 100%);
        border-radius: 12px;
        padding: 48px;
        box-shadow:
          0 24px 80px rgba(139, 69, 19, 0.2),
          0 12px 30px rgba(139, 69, 19, 0.15),
          inset 0 1px 0 rgba(255, 255, 255, 0.5);
        border: 2px solid rgba(139, 69, 19, 0.3);
        position: relative;
        overflow: hidden;
      }
      .card-wrapper::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #8b4513, #cd853f, #8b4513);
      }
      .card-wrapper::after {
        content: '';
        position: absolute;
        top: 20px;
        left: 20px;
        right: 20px;
        bottom: 20px;
        border: 1px solid rgba(139, 69, 19, 0.2);
        pointer-events: none;
      }
      .card-theme {
        font-size: 2.2rem;
        font-weight: 700;
        color: #8b4513;
        letter-spacing: 2px;
        margin-bottom: 12px;
        text-shadow: 2px 2px 4px rgba(139, 69, 19, 0.2);
      }
      .card-tagline {
        font-size: 1rem;
        letter-spacing: 0.3em;
        color: rgba(139, 69, 19, 0.7);
        margin-bottom: 20px;
        font-weight: 500;
      }
      .card-question {
        font-size: 1.05rem;
        line-height: 1.8;
        color: rgba(60, 40, 20, 0.85);
        margin-top: 20px;
        padding: 16px 20px;
        background: rgba(245, 230, 211, 0.8);
        border-radius: 8px;
        border: 1px solid rgba(139, 69, 19, 0.3);
        border-left: 4px solid rgba(139, 69, 19, 0.6);
        font-style: normal;
      }
      .card-section {
        background: rgba(255, 250, 240, 0.9);
        border-radius: 8px;
        padding: 24px 28px;
        margin-bottom: 20px;
        border: 1px solid rgba(139, 69, 19, 0.25);
        box-shadow: 0 4px 12px rgba(139, 69, 19, 0.1);
        border-left: 4px solid var(--section-accent, rgba(139, 69, 19, 0.6));
      }
      .section-title {
        color: rgba(80, 50, 20, 0.9);
        font-weight: 600;
      }
      .section-content {
        color: rgba(60, 40, 20, 0.85);
      }
      .card-date {
        color: rgba(139, 69, 19, 0.6);
      }
      .card-label {
        color: rgba(139, 69, 19, 0.6);
      }
      .card-list li::before {
        content: '❀';
        position: absolute;
        left: 0;
        color: rgba(139, 69, 19, 0.7);
      }
      .card-footer span {
        display: inline-block;
        padding: 8px 18px;
        border-radius: 4px;
        background: rgba(245, 230, 211, 0.9);
        border: 1px solid rgba(139, 69, 19, 0.4);
        color: rgba(139, 69, 19, 0.8);
      }
      .card-markdown a,
      .section-content a {
        color: #8b4513;
        text-decoration: none;
        border-bottom: 1px solid rgba(139, 69, 19, 0.5);
      }
    `,
    'sci-fi': `
      :root {
        font-size: 16px;
        color-scheme: dark;
      }
      * {
        box-sizing: border-box;
      }
      body {
        margin: 0;
        padding: 0;
        font-family: 'Segoe UI', 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif;
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 48px 24px;
        position: relative;
        overflow: hidden;
      }
      body::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
          linear-gradient(0deg, transparent 24%, rgba(0, 255, 255, 0.03) 25%, rgba(0, 255, 255, 0.03) 26%, transparent 27%, transparent 74%, rgba(0, 255, 255, 0.03) 75%, rgba(0, 255, 255, 0.03) 76%, transparent 77%, transparent),
          linear-gradient(90deg, transparent 24%, rgba(0, 255, 255, 0.03) 25%, rgba(0, 255, 255, 0.03) 26%, transparent 27%, transparent 74%, rgba(0, 255, 255, 0.03) 75%, rgba(0, 255, 255, 0.03) 76%, transparent 77%, transparent);
        background-size: 50px 50px;
        animation: gridMove 20s linear infinite;
        pointer-events: none;
      }
      @keyframes gridMove {
        0% { transform: translate(0, 0); }
        100% { transform: translate(50px, 50px); }
      }
      .card-wrapper {
        width: min(860px, 100%);
        background: rgba(10, 15, 30, 0.9);
        border-radius: 16px;
        padding: 48px;
        box-shadow:
          0 24px 80px rgba(0, 255, 255, 0.2),
          0 0 0 1px rgba(0, 255, 255, 0.3),
          inset 0 0 40px rgba(0, 255, 255, 0.1);
        border: 2px solid rgba(0, 255, 255, 0.4);
        position: relative;
        overflow: hidden;
      }
      .card-wrapper::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, #00ffff, transparent);
        animation: scanLine 3s linear infinite;
      }
      @keyframes scanLine {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
      }
      .card-theme {
        font-size: 2rem;
        font-weight: 700;
        color: #00ffff;
        letter-spacing: 2px;
        margin-bottom: 12px;
        text-shadow: 0 0 10px #00ffff, 0 0 20px #00ffff;
        font-family: 'Courier New', monospace;
      }
      .card-tagline {
        font-size: 1rem;
        letter-spacing: 0.3em;
        text-transform: uppercase;
        color: rgba(0, 255, 255, 0.7);
        margin-bottom: 20px;
        font-family: 'Courier New', monospace;
      }
      .card-question {
        font-size: 1.05rem;
        line-height: 1.7;
        color: rgba(200, 255, 255, 0.9);
        margin-top: 20px;
        padding: 16px 20px;
        background: rgba(0, 255, 255, 0.1);
        border-radius: 8px;
        border: 1px solid rgba(0, 255, 255, 0.3);
        border-left: 3px solid rgba(0, 255, 255, 0.6);
        font-style: normal;
        font-family: 'Courier New', monospace;
      }
      .card-section {
        background: rgba(15, 20, 35, 0.8);
        border-radius: 12px;
        padding: 24px 28px;
        margin-bottom: 20px;
        border: 1px solid rgba(0, 255, 255, 0.2);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4), inset 0 0 20px rgba(0, 255, 255, 0.05);
        border-left: 4px solid var(--section-accent, rgba(0, 255, 255, 0.6));
      }
      .section-title {
        color: rgba(0, 255, 255, 0.9);
        font-weight: 600;
      }
      .section-content {
        color: rgba(200, 255, 255, 0.85);
      }
      .card-date {
        color: rgba(0, 255, 255, 0.6);
      }
      .card-label {
        color: rgba(0, 255, 255, 0.6);
      }
      .card-list li::before {
        content: '◆';
        position: absolute;
        left: 0;
        color: rgba(0, 255, 255, 0.7);
      }
      .card-footer span {
        display: inline-block;
        padding: 8px 18px;
        border-radius: 4px;
        background: rgba(0, 255, 255, 0.1);
        border: 1px solid rgba(0, 255, 255, 0.4);
        color: rgba(0, 255, 255, 0.8);
        font-family: 'Courier New', monospace;
      }
      .card-markdown a,
      .section-content a {
        color: #00ffff;
        text-decoration: none;
        border-bottom: 1px solid rgba(0, 255, 255, 0.5);
      }
    `,
    candy: `
      :root {
        font-size: 16px;
        color-scheme: light;
      }
      * {
        box-sizing: border-box;
      }
      body {
        margin: 0;
        padding: 0;
        font-family: 'Source Han Serif SC', 'Noto Serif SC', 'Segoe UI', 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif;
        background: linear-gradient(135deg, #ffeef8 0%, #fff0f5 25%, #ffe4e1 50%, #fff8dc 75%, #f0fff0 100%);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 48px 24px;
        position: relative;
      }
      @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
      }
      body::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
          radial-gradient(circle at 20% 30%, rgba(255, 182, 193, 0.3) 0%, transparent 50%),
          radial-gradient(circle at 80% 70%, rgba(255, 192, 203, 0.3) 0%, transparent 50%),
          radial-gradient(circle at 50% 50%, rgba(255, 218, 185, 0.2) 0%, transparent 50%);
        pointer-events: none;
      }
      .card-wrapper {
        width: min(860px, 100%);
        background: rgba(255, 255, 255, 0.98);
        border-radius: 32px;
        padding: 48px;
        box-shadow:
          0 24px 80px rgba(255, 182, 193, 0.3),
          0 12px 30px rgba(255, 192, 203, 0.2),
          inset 0 2px 0 rgba(255, 255, 255, 0.9);
        border: 3px solid rgba(255, 182, 193, 0.4);
        position: relative;
        overflow: hidden;
      }
      .card-wrapper::before {
        content: '';
        position: absolute;
        top: -50px;
        right: -50px;
        width: 200px;
        height: 200px;
        background: radial-gradient(circle, rgba(255, 182, 193, 0.4), transparent 70%);
        filter: blur(30px);
        animation: float 6s ease-in-out infinite;
      }
      .card-wrapper::after {
        content: '';
        position: absolute;
        bottom: -40px;
        left: -40px;
        width: 180px;
        height: 180px;
        background: radial-gradient(circle, rgba(255, 218, 185, 0.4), transparent 70%);
        filter: blur(30px);
        animation: float 8s ease-in-out infinite reverse;
      }
      @keyframes float {
        0%, 100% { transform: translate(0, 0) scale(1); }
        50% { transform: translate(10px, -10px) scale(1.1); }
      }
      .card-theme {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #ff69b4, #ff1493, #ff69b4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: 1px;
        margin-bottom: 12px;
      }
      .card-tagline {
        font-size: 1rem;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        color: rgba(255, 105, 180, 0.7);
        margin-bottom: 20px;
        font-weight: 500;
      }
      .card-question {
        font-size: 1.05rem;
        line-height: 1.7;
        color: rgba(0, 0, 0, 0.75);
        margin-top: 20px;
        padding: 16px 20px;
        background: linear-gradient(135deg, rgba(255, 182, 193, 0.3), rgba(255, 192, 203, 0.3));
        border-radius: 20px;
        border: 2px dashed rgba(255, 105, 180, 0.4);
        font-style: italic;
      }
      .card-section {
        background: linear-gradient(135deg, rgba(255, 250, 250, 0.95), rgba(255, 245, 250, 0.95));
        border-radius: 24px;
        padding: 24px 28px;
        margin-bottom: 20px;
        border: 2px solid rgba(255, 182, 193, 0.3);
        box-shadow: 0 12px 30px rgba(255, 182, 193, 0.15);
        border-left: 5px solid var(--section-accent, rgba(255, 105, 180, 0.7));
      }
      .card-list li::before {
        content: '🍬';
        position: absolute;
        left: 0;
        font-size: 1.1em;
      }
      .card-footer span {
        display: inline-block;
        padding: 8px 18px;
        border-radius: 999px;
        background: linear-gradient(135deg, rgba(255, 182, 193, 0.3), rgba(255, 192, 203, 0.3));
        border: 2px solid rgba(255, 105, 180, 0.4);
        color: rgba(255, 105, 180, 0.9);
      }
      .card-markdown a,
      .section-content a {
        color: #ff69b4;
        text-decoration: none;
        border-bottom: 2px dashed rgba(255, 105, 180, 0.5);
      }
    `
  }
  return templates[template]
}

// 通用样式（所有模板共享）
const getCommonStyles = (): string => {
  return `
    .card-content {
      position: relative;
      z-index: 1;
    }
    header {
      text-align: center;
      margin-bottom: 40px;
    }
    .card-date {
      font-size: 0.95rem;
      color: rgba(0, 0, 0, 0.45);
    }
    .section-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;
    }
    .section-icon {
      font-size: 1.5rem;
    }
    .section-title {
      font-size: 1.1rem;
      font-weight: 600;
      color: rgba(0, 0, 0, 0.8);
    }
    .section-content {
      line-height: 1.9;
      color: rgba(0, 0, 0, 0.75);
      font-size: 1rem;
    }
    .card-two-column {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 20px;
    }
    .card-label {
      font-size: 0.85rem;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: rgba(0, 0, 0, 0.45);
      margin-bottom: 6px;
    }
    .card-markdown :is(p, ul, ol) {
      margin: 0 0 10px;
    }
    .card-markdown ul,
    .card-markdown ol,
    .section-content ul,
    .section-content ol {
      padding-left: 24px;
    }
    .section-content li {
      margin-bottom: 8px;
    }
    .card-list {
      list-style: none;
      margin: 0;
      padding: 0;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .card-list li {
      padding-left: 20px;
      position: relative;
    }
    .card-footer {
      text-align: center;
      margin-top: 32px;
      font-size: 0.9rem;
      color: rgba(0, 0, 0, 0.4);
      letter-spacing: 0.2em;
    }
    .card-markdown code,
    .section-content code {
      background: rgba(0, 0, 0, 0.04);
      padding: 2px 6px;
      border-radius: 6px;
      font-size: 0.9em;
    }
    @media (max-width: 640px) {
      body {
        padding: 24px 16px;
      }
      .card-wrapper {
        padding: 32px 20px;
      }
    }
  `
}

export const generateCardHtml = (cardData: CardData, template: CardTemplate = 'basic') => {
  const title = cardData.theme?.trim() || '心灵之卡'
  const date = formatDate()
  const useThreePart = shouldUseThreePart(cardData)
  const sectionsHtml = useThreePart ? buildThreePartSections(cardData) : buildFiveStepSections(cardData)
  const userQuestion = cardData.user_question?.trim()
  const templateStyles = getTemplateStyles(template)
  const commonStyles = getCommonStyles()

  return `<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>${title}</title>
    <style>
      ${templateStyles}
      ${commonStyles}
    </style>
  </head>
  <body>
    <div class="card-wrapper">
      <div class="card-content">
        <header>
          <div class="card-theme">${title}</div>
          <div class="card-tagline">LOVE · YOURSELF · MOMENTS</div>
          <div class="card-date">${date}</div>
          ${userQuestion ? `<div class="card-question">${renderMarkdown(userQuestion)}</div>` : ''}
        </header>
        ${sectionsHtml}
        <div class="card-footer">
          <span>栀情屿 · 筑一方温柔心岛</span>
        </div>
      </div>
    </div>
  </body>
</html>`
}

