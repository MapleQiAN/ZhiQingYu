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
        padding: 48px 24px;
        font-family: 'Source Han Serif SC', 'Noto Serif SC', 'Segoe UI', 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif;
        background: #0a0e27;
        min-height: 100vh;
        position: relative;
        overflow-x: hidden;
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
          radial-gradient(1px 1px at 55% 80%, white, transparent),
          radial-gradient(3px 3px at 10% 20%, rgba(150, 200, 255, 0.8), transparent),
          radial-gradient(2px 2px at 70% 80%, rgba(200, 150, 255, 0.6), transparent),
          radial-gradient(1px 1px at 40% 90%, white, transparent);
        background-size: 200% 200%;
        background-position: 0% 0%;
        animation: starMove 20s linear infinite;
        opacity: 0.6;
        pointer-events: none;
        z-index: 0;
      }
      @keyframes starMove {
        0% { background-position: 0% 0%; }
        100% { background-position: 100% 100%; }
      }
      body::after {
        content: '🌙 ⭐ 🌟 ✨ 🌌';
        position: fixed;
        top: 15%;
        right: 8%;
        font-size: 50px;
        opacity: 0.15;
        transform: rotate(20deg);
        pointer-events: none;
        z-index: 0;
        white-space: nowrap;
        animation: float 6s ease-in-out infinite;
      }
      @keyframes float {
        0%, 100% { transform: rotate(20deg) translateY(0); }
        50% { transform: rotate(20deg) translateY(-20px); }
      }
      .card-wrapper {
        width: min(860px, 100%);
        margin: 0 auto;
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
        z-index: 1;
      }
      .card-wrapper::before {
        content: '🌠';
        position: absolute;
        top: 30px;
        left: 30px;
        font-size: 80px;
        opacity: 0.2;
        transform: rotate(-15deg);
        pointer-events: none;
        animation: twinkle 3s ease-in-out infinite;
      }
      @keyframes twinkle {
        0%, 100% { opacity: 0.2; transform: rotate(-15deg) scale(1); }
        50% { opacity: 0.4; transform: rotate(-15deg) scale(1.1); }
      }
      .card-wrapper::after {
        content: '⭐';
        position: absolute;
        bottom: 40px;
        right: 50px;
        font-size: 60px;
        opacity: 0.25;
        transform: rotate(25deg);
        pointer-events: none;
        animation: twinkle 4s ease-in-out infinite reverse;
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
        padding: 48px 24px;
        font-family: 'Source Han Serif SC', 'Noto Serif SC', 'Segoe UI', 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif;
        background: #e0f2fe;
        min-height: 100vh;
        position: relative;
        overflow-x: hidden;
      }
      body::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
          url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M50 50 L60 30 L80 50 L60 70 Z' fill='%2364b5f6' fill-opacity='0.1'/%3E%3Cpath d='M20 20 L30 10 L40 20 L30 30 Z' fill='%234fc3f7' fill-opacity='0.15'/%3E%3Cpath d='M80 80 L90 70 L100 80 L90 90 Z' fill='%232196f3' fill-opacity='0.1'/%3E%3C/svg%3E"),
          url("data:image/svg+xml,%3Csvg width='80' height='80' viewBox='0 0 80 80' xmlns='http://www.w3.org/2000/svg'%3E%3Ccircle cx='40' cy='40' r='15' fill='%234fc3f7' fill-opacity='0.08'/%3E%3Ccircle cx='10' cy='10' r='8' fill='%2364b5f6' fill-opacity='0.12'/%3E%3Ccircle cx='70' cy='70' r='12' fill='%232196f3' fill-opacity='0.1'/%3E%3C/svg%3E");
        background-size: 200px 200px, 150px 150px;
        background-position: 0 0, 100px 100px;
        pointer-events: none;
        z-index: 0;
        animation: wave 8s ease-in-out infinite;
      }
      @keyframes wave {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
      }
      body::after {
        content: '🌊 🐚 🌊 💙 🌊';
        position: fixed;
        bottom: 10%;
        left: 5%;
        font-size: 45px;
        opacity: 0.12;
        transform: rotate(-10deg);
        pointer-events: none;
        z-index: 0;
        white-space: nowrap;
      }
      .card-wrapper {
        width: min(860px, 100%);
        margin: 0 auto;
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
        z-index: 1;
      }
      .card-wrapper::before {
        content: '🌊';
        position: absolute;
        top: 25px;
        right: 35px;
        font-size: 70px;
        opacity: 0.15;
        transform: rotate(15deg);
        pointer-events: none;
        animation: floatWave 5s ease-in-out infinite;
      }
      @keyframes floatWave {
        0%, 100% { transform: rotate(15deg) translateY(0); }
        50% { transform: rotate(15deg) translateY(-15px); }
      }
      .card-wrapper::after {
        content: '🐚';
        position: absolute;
        bottom: 35px;
        left: 45px;
        font-size: 55px;
        opacity: 0.18;
        transform: rotate(-25deg);
        pointer-events: none;
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
        padding: 48px 24px;
        font-family: 'KaiTi', 'STKaiti', 'Source Han Serif SC', 'Noto Serif SC', 'Microsoft YaHei', serif;
        background: linear-gradient(135deg, #fef2f2 0%, #fff7ed 30%, #fef3c7 60%, #fce7f3 100%);
        min-height: 100vh;
        position: relative;
        overflow-x: hidden;
      }
      body::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
          url("data:image/svg+xml,%3Csvg width='400' height='500' viewBox='0 0 400 500' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' stroke='%23ec4899' stroke-opacity='0.12' stroke-width='2'%3E%3Cpath d='M200 450 Q180 400 160 420 Q140 440 160 460 Q180 480 200 450'/%3E%3Cpath d='M200 350 Q220 300 240 320 Q260 340 240 360 Q220 380 200 350'/%3E%3Cpath d='M200 250 Q180 200 160 220 Q140 240 160 260 Q180 280 200 250'/%3E%3Cpath d='M200 150 Q220 100 240 120 Q260 140 240 160 Q220 180 200 150'/%3E%3C/g%3E%3Cg fill='%23f472b6' fill-opacity='0.15'%3E%3Cpath d='M200 400 Q190 380 185 390 Q180 400 190 410 Q200 420 210 410 Q220 400 215 390 Q210 380 200 400'/%3E%3Cpath d='M200 300 Q190 280 185 290 Q180 300 190 310 Q200 320 210 310 Q220 300 215 290 Q210 280 200 300'/%3E%3Cpath d='M200 200 Q190 180 185 190 Q180 200 190 210 Q200 220 210 210 Q220 200 215 190 Q210 180 200 200'/%3E%3Cpath d='M200 100 Q190 80 185 90 Q180 100 190 110 Q200 120 210 110 Q220 100 215 90 Q210 80 200 100'/%3E%3C/g%3E%3Cg fill='%23f59e0b' fill-opacity='0.1'%3E%3Ccircle cx='150' cy='380' r='12'/%3E%3Ccircle cx='250' cy='320' r='10'/%3E%3Ccircle cx='140' cy='280' r='11'/%3E%3Ccircle cx='260' cy='220' r='9'/%3E%3Ccircle cx='145' cy='180' r='10'/%3E%3Ccircle cx='255' cy='120' r='8'/%3E%3C/g%3E%3C/svg%3E"),
          url("data:image/svg+xml,%3Csvg width='350' height='350' viewBox='0 0 350 350' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' stroke='%23dc2626' stroke-opacity='0.1' stroke-width='1.5'%3E%3Cpath d='M175 300 Q200 250 225 280 T275 300'/%3E%3Cpath d='M175 250 Q200 200 225 230 T275 250'/%3E%3Cpath d='M175 200 Q200 150 225 180 T275 200'/%3E%3Cpath d='M175 150 Q200 100 225 130 T275 150'/%3E%3Cpath d='M175 100 Q200 50 225 80 T275 100'/%3E%3C/g%3E%3Cg fill='%23f472b6' fill-opacity='0.12'%3E%3Cpath d='M100 200 Q120 180 140 200 Q160 220 140 240 Q120 260 100 240 Q80 220 100 200'/%3E%3Cpath d='M250 200 Q270 180 290 200 Q310 220 290 240 Q270 260 250 240 Q230 220 250 200'/%3E%3Cpath d='M100 100 Q120 80 140 100 Q160 120 140 140 Q120 160 100 140 Q80 120 100 100'/%3E%3Cpath d='M250 100 Q270 80 290 100 Q310 120 290 140 Q270 160 250 140 Q230 120 250 100'/%3E%3C/g%3E%3Cg fill='%23fbbf24' fill-opacity='0.15'%3E%3Ccircle cx='80' cy='250' r='8'/%3E%3Ccircle cx='270' cy='200' r='7'/%3E%3Ccircle cx='75' cy='150' r='9'/%3E%3Ccircle cx='275' cy='100' r='6'/%3E%3C/g%3E%3C/svg%3E"),
          url("data:image/svg+xml,%3Csvg width='250' height='250' viewBox='0 0 250 250' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' stroke='%23eab308' stroke-opacity='0.08' stroke-width='1.2'%3E%3Cpath d='M50 200 Q60 180 80 190 Q100 200 90 220 Q80 240 60 230 Q40 220 50 200'/%3E%3Cpath d='M200 200 Q210 180 230 190 Q250 200 240 220 Q230 240 210 230 Q190 220 200 200'/%3E%3Cpath d='M50 50 Q60 30 80 40 Q100 50 90 70 Q80 90 60 80 Q40 70 50 50'/%3E%3Cpath d='M200 50 Q210 30 230 40 Q250 50 240 70 Q230 90 210 80 Q190 70 200 50'/%3E%3C/g%3E%3Cg fill='%23f59e0b' fill-opacity='0.1'%3E%3Cpath d='M125 200 Q135 190 145 200 Q155 210 145 220 Q135 230 125 220 Q115 210 125 200'/%3E%3Cpath d='M125 50 Q135 40 145 50 Q155 60 145 70 Q135 80 125 70 Q115 60 125 50'/%3E%3C/g%3E%3C/svg%3E");
        background-size: 500px 625px, 450px 450px, 350px 350px;
        background-position: 0 0, 300px 150px, 100px 300px;
        pointer-events: none;
        z-index: 0;
      }
      body::after {
        content: '';
        position: fixed;
        top: 8%;
        right: 5%;
        width: 200px;
        height: 200px;
        background-image: url("data:image/svg+xml,%3Csvg width='200' height='200' viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' stroke='%23ec4899' stroke-opacity='0.15' stroke-width='2'%3E%3Cpath d='M100 180 Q80 160 60 180 Q40 200 60 200 Q80 200 100 180'/%3E%3Cpath d='M100 120 Q80 100 60 120 Q40 140 60 140 Q80 140 100 120'/%3E%3Cpath d='M100 60 Q80 40 60 60 Q40 80 60 80 Q80 80 100 60'/%3E%3C/g%3E%3Cg fill='%23f472b6' fill-opacity='0.2'%3E%3Cpath d='M100 150 Q95 140 90 145 Q85 150 90 155 Q95 160 100 150'/%3E%3Cpath d='M100 90 Q95 80 90 85 Q85 90 90 95 Q95 100 100 90'/%3E%3Cpath d='M100 30 Q95 20 90 25 Q85 30 90 35 Q95 40 100 30'/%3E%3C/g%3E%3Cg fill='%23fbbf24' fill-opacity='0.18'%3E%3Ccircle cx='140' cy='150' r='8'/%3E%3Ccircle cx='140' cy='90' r='7'/%3E%3Ccircle cx='140' cy='30' r='6'/%3E%3C/g%3E%3C/svg%3E");
        background-size: contain;
        background-repeat: no-repeat;
        opacity: 0.7;
        pointer-events: none;
        z-index: 0;
        transform: rotate(15deg);
      }
      .card-wrapper {
        width: min(860px, 100%);
        margin: 0 auto;
        background: rgba(255, 255, 255, 0.98);
        border-radius: 12px;
        padding: 48px;
        box-shadow:
          0 24px 80px rgba(236, 72, 153, 0.15),
          0 12px 30px rgba(220, 38, 38, 0.12),
          0 4px 12px rgba(245, 158, 11, 0.1),
          inset 0 1px 0 rgba(255, 255, 255, 0.9);
        border: 2px solid rgba(236, 72, 153, 0.2);
        position: relative;
        overflow: hidden;
        z-index: 1;
      }
      .card-wrapper::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, 
          transparent 0%, 
          rgba(236, 72, 153, 0.4) 15%, 
          rgba(220, 38, 38, 0.5) 30%,
          rgba(245, 158, 11, 0.6) 50%,
          rgba(220, 38, 38, 0.5) 70%,
          rgba(236, 72, 153, 0.4) 85%, 
          transparent 100%);
      }
      .card-wrapper::after {
        content: '';
        position: absolute;
        top: 15px;
        right: 25px;
        width: 90px;
        height: 90px;
        background-image: url("data:image/svg+xml,%3Csvg width='90' height='90' viewBox='0 0 90 90' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' stroke='%23ec4899' stroke-opacity='0.2' stroke-width='2'%3E%3Cpath d='M45 70 Q35 50 25 60 Q15 70 25 75 Q35 80 45 70'/%3E%3Cpath d='M45 50 Q55 30 65 40 Q75 50 65 55 Q55 60 45 50'/%3E%3Cpath d='M45 30 Q35 10 25 20 Q15 30 25 35 Q35 40 45 30'/%3E%3C/g%3E%3Cg fill='%23f472b6' fill-opacity='0.25'%3E%3Cpath d='M45 60 Q42 55 40 57 Q38 59 40 62 Q42 65 45 60'/%3E%3Cpath d='M45 40 Q48 35 50 37 Q52 39 50 42 Q48 45 45 40'/%3E%3Cpath d='M45 20 Q42 15 40 17 Q38 19 40 22 Q42 25 45 20'/%3E%3C/g%3E%3Cg fill='%23fbbf24' fill-opacity='0.3'%3E%3Ccircle cx='30' cy='65' r='5'/%3E%3Ccircle cx='60' cy='45' r='4'/%3E%3Ccircle cx='28' cy='25' r='4.5'/%3E%3C/g%3E%3C/svg%3E");
        background-size: contain;
        background-repeat: no-repeat;
        opacity: 0.8;
        pointer-events: none;
        transform: rotate(12deg);
      }
      .card-theme {
        font-size: 2.2rem;
        font-weight: 700;
        color: #dc2626;
        letter-spacing: 2px;
        margin-bottom: 12px;
        text-shadow: 1px 1px 3px rgba(236, 72, 153, 0.2), 0 0 8px rgba(245, 158, 11, 0.15);
      }
      .card-tagline {
        font-size: 1rem;
        letter-spacing: 0.3em;
        color: rgba(236, 72, 153, 0.7);
        margin-bottom: 20px;
        font-weight: 500;
      }
      .card-question {
        font-size: 1.05rem;
        line-height: 1.8;
        color: rgba(30, 30, 30, 0.85);
        margin-top: 20px;
        padding: 16px 20px;
        background: linear-gradient(135deg, rgba(254, 242, 242, 0.8) 0%, rgba(255, 247, 237, 0.8) 100%);
        border-radius: 8px;
        border: 1px solid rgba(236, 72, 153, 0.2);
        border-left: 3px solid rgba(236, 72, 153, 0.5);
        font-style: normal;
        box-shadow: 0 2px 6px rgba(236, 72, 153, 0.1);
      }
      .card-section {
        background: linear-gradient(135deg, rgba(255, 247, 237, 0.9) 0%, rgba(254, 243, 199, 0.9) 100%);
        border-radius: 8px;
        padding: 24px 28px;
        margin-bottom: 20px;
        border: 1px solid rgba(245, 158, 11, 0.2);
        box-shadow: 0 2px 8px rgba(245, 158, 11, 0.1);
        border-left: 3px solid var(--section-accent, rgba(236, 72, 153, 0.5));
      }
      .section-title {
        color: rgba(220, 38, 38, 0.9);
        font-weight: 600;
      }
      .section-content {
        color: rgba(30, 30, 30, 0.85);
      }
      .card-date {
        color: rgba(236, 72, 153, 0.7);
      }
      .card-label {
        color: rgba(236, 72, 153, 0.7);
      }
      .card-list li::before {
        content: '·';
        position: absolute;
        left: 0;
        color: rgba(236, 72, 153, 0.6);
        font-size: 1.5em;
        font-weight: bold;
      }
      .card-footer span {
        display: inline-block;
        padding: 8px 18px;
        border-radius: 6px;
        background: linear-gradient(135deg, rgba(254, 242, 242, 0.9) 0%, rgba(252, 231, 243, 0.9) 100%);
        border: 1px solid rgba(236, 72, 153, 0.3);
        color: rgba(220, 38, 38, 0.8);
        box-shadow: 0 2px 4px rgba(236, 72, 153, 0.15);
      }
      .card-markdown a,
      .section-content a {
        color: #dc2626;
        text-decoration: none;
        border-bottom: 1px solid rgba(236, 72, 153, 0.5);
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
        padding: 48px 24px;
        font-family: 'Segoe UI', 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif;
        background: #0a0a0a;
        min-height: 100vh;
        position: relative;
        overflow-x: hidden;
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
          linear-gradient(90deg, transparent 24%, rgba(0, 255, 255, 0.03) 25%, rgba(0, 255, 255, 0.03) 26%, transparent 27%, transparent 74%, rgba(0, 255, 255, 0.03) 75%, rgba(0, 255, 255, 0.03) 76%, transparent 77%, transparent),
          url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' stroke='%2300ffff' stroke-opacity='0.1' stroke-width='1'%3E%3Cpath d='M30 0 L30 60 M0 30 L60 30'/%3E%3Ccircle cx='30' cy='30' r='20'/%3E%3C/g%3E%3C/svg%3E"),
          url("data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cpolygon points='20,5 35,35 5,35' fill='%2300ffff' fill-opacity='0.08'/%3E%3C/svg%3E");
        background-size: 50px 50px, 50px 50px, 120px 120px, 80px 80px;
        background-position: 0 0, 0 0, 0 0, 60px 60px;
        animation: gridMove 20s linear infinite;
        pointer-events: none;
        z-index: 0;
      }
      @keyframes gridMove {
        0% { transform: translate(0, 0); }
        100% { transform: translate(50px, 50px); }
      }
      body::after {
        content: '🚀 ⚡ 🔮 🌌 💫';
        position: fixed;
        top: 10%;
        left: 5%;
        font-size: 45px;
        opacity: 0.12;
        transform: rotate(-15deg);
        pointer-events: none;
        z-index: 0;
        white-space: nowrap;
      }
      .card-wrapper {
        width: min(860px, 100%);
        margin: 0 auto;
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
        z-index: 1;
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
      .card-wrapper::after {
        content: '⚡';
        position: absolute;
        top: 30px;
        right: 40px;
        font-size: 70px;
        opacity: 0.15;
        transform: rotate(45deg);
        pointer-events: none;
        animation: pulse 2s ease-in-out infinite;
      }
      @keyframes pulse {
        0%, 100% { opacity: 0.15; transform: rotate(45deg) scale(1); }
        50% { opacity: 0.25; transform: rotate(45deg) scale(1.1); }
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
        padding: 48px 24px;
        font-family: 'Source Han Serif SC', 'Noto Serif SC', 'Segoe UI', 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif;
        background: #ffeef8;
        min-height: 100vh;
        position: relative;
        overflow-x: hidden;
      }
      body::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
          url("data:image/svg+xml,%3Csvg width='80' height='80' viewBox='0 0 80 80' xmlns='http://www.w3.org/2000/svg'%3E%3Ccircle cx='40' cy='40' r='20' fill='%23ffb6c1' fill-opacity='0.15'/%3E%3Ccircle cx='20' cy='20' r='12' fill='%23ffc0cb' fill-opacity='0.2'/%3E%3Ccircle cx='60' cy='60' r='15' fill='%23ffdab9' fill-opacity='0.18'/%3E%3C/svg%3E"),
          url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cpolygon points='30,5 50,50 10,50' fill='%23ffb6c1' fill-opacity='0.12'/%3E%3Cpolygon points='30,55 45,20 15,20' fill='%23ffc0cb' fill-opacity='0.15'/%3E%3C/svg%3E"),
          url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M50 50 L60 30 L80 50 L60 70 Z' fill='%23ffdab9' fill-opacity='0.1'/%3E%3Cpath d='M20 20 L30 10 L40 20 L30 30 Z' fill='%23ffb6c1' fill-opacity='0.12'/%3E%3C/svg%3E");
        background-size: 160px 160px, 120px 120px, 200px 200px;
        background-position: 0 0, 80px 80px, 40px 40px;
        pointer-events: none;
        z-index: 0;
        animation: candyFloat 20s ease-in-out infinite;
      }
      @keyframes candyFloat {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-20px); }
      }
      body::after {
        content: '🍭 🍬 🍰 🎂 🍡';
        position: fixed;
        top: 8%;
        left: 3%;
        font-size: 50px;
        opacity: 0.15;
        transform: rotate(-12deg);
        pointer-events: none;
        z-index: 0;
        white-space: nowrap;
      }
      .card-wrapper {
        width: min(860px, 100%);
        margin: 0 auto;
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
        z-index: 1;
      }
      .card-wrapper::before {
        content: '🍭';
        position: absolute;
        top: 20px;
        right: 30px;
        font-size: 75px;
        opacity: 0.2;
        transform: rotate(20deg);
        pointer-events: none;
        animation: candyBounce 4s ease-in-out infinite;
      }
      @keyframes candyBounce {
        0%, 100% { transform: rotate(20deg) translateY(0); }
        50% { transform: rotate(20deg) translateY(-10px); }
      }
      .card-wrapper::after {
        content: '🍬';
        position: absolute;
        bottom: 35px;
        left: 45px;
        font-size: 60px;
        opacity: 0.22;
        transform: rotate(-25deg);
        pointer-events: none;
        animation: candyBounce 5s ease-in-out infinite reverse;
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

