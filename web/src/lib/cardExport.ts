import type { CardData } from './api'
import { renderMarkdown } from './markdown'

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

export const generateCardHtml = (cardData: CardData) => {
  const title = cardData.theme?.trim() || '心灵之卡'
  const date = formatDate()
  const useThreePart = shouldUseThreePart(cardData)
  const sectionsHtml = useThreePart ? buildThreePartSections(cardData) : buildFiveStepSections(cardData)
  const userQuestion = cardData.user_question?.trim()

  return `<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>${title}</title>
    <style>
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
      .card-content {
        position: relative;
        z-index: 1;
      }
      header {
        text-align: center;
        margin-bottom: 40px;
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
      .card-date {
        font-size: 0.95rem;
        color: rgba(0, 0, 0, 0.45);
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
      .card-list li::before {
        content: '✦';
        position: absolute;
        left: 0;
        color: rgba(194, 85, 107, 0.6);
      }
      .card-footer {
        text-align: center;
        margin-top: 32px;
        font-size: 0.9rem;
        color: rgba(0, 0, 0, 0.4);
        letter-spacing: 0.2em;
      }
      .card-footer span {
        display: inline-block;
        padding: 8px 18px;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.8);
        border: 1px solid rgba(232, 180, 184, 0.4);
      }
      .card-markdown code,
      .section-content code {
        background: rgba(0, 0, 0, 0.04);
        padding: 2px 6px;
        border-radius: 6px;
        font-size: 0.9em;
      }
      .card-markdown a,
      .section-content a {
        color: #c2556b;
        text-decoration: none;
        border-bottom: 1px solid rgba(194, 85, 107, 0.4);
      }
      @media (max-width: 640px) {
        body {
          padding: 24px 16px;
        }
        .card-wrapper {
          padding: 32px 20px;
        }
      }
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

