/**
 * API调用封装
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface ApiResponse<T> {
  data: T | null
  error: {
    code: string
    message: string
  } | null
}

export interface CardData {
  theme?: string
  useThreePart?: boolean  // 是否使用简洁模式（3卡片），false表示使用5步骤模式（5卡片）
  user_question?: string  // 用户提问内容（可以是多轮对话后总结的疑问，也可以是用户直接提出的问题）
  // 简洁模式（3卡片）字段
  emotion_echo?: string
  clarification?: string
  suggestion?: string[] | string
  // 5步骤模式（5卡片）字段
  step1_emotion_mirror?: string  // Step 1: 情绪镜像
  step1_problem_restate?: string  // Step 1: 问题复述
  step2_breakdown?: string  // Step 2: 问题拆解
  step3_explanation?: string  // Step 3: 专业解释
  step4_suggestions?: string[] | string  // Step 4: 行动建议
  step5_summary?: string  // Step 5: 收尾小结
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  card_data?: CardData | null
  should_show_card_button?: boolean  // 是否显示"开始关心吧！"按钮
  should_show_satisfaction_buttons?: boolean  // 是否显示"满意/不满意"按钮
}

export interface ChatRequest {
  session_id?: string | null
  messages: ChatMessage[]
  experience_mode?: 'A' | 'B' | 'C' | 'D' | null  // 体验模式：A:只想被听 B:想搞懂 C:想要建议 D:系统深聊
  ai_style?: string | null  // AI风格：comfort, analyst, coach, mentor, friend, listener, growth, crisis_safe
  chat_mode?: 'deep' | 'quick' | null  // 聊天模式：deep(深聊模式) 或 quick(快速模式)
}

export interface ChatResponse {
  session_id: string
  reply: string
  emotion: string
  intensity: number
  topics: string[]
  risk_level: 'normal' | 'high'  // 后端返回的是normal/high，但内部可能是low/medium/high
  card_data?: CardData | null
  should_show_card_button?: boolean  // 是否显示"开始关心吧！"按钮
  should_show_satisfaction_buttons?: boolean  // 是否显示"满意/不满意"按钮
}

export interface DailySummaryItem {
  date: string
  summary_text: string | null
  main_emotion: string | null
  avg_intensity: number | null
}

export interface DailyListResponse {
  items: DailySummaryItem[]
}

export interface MessageItem {
  id: number
  role: string
  content: string
  emotion: string | null
  intensity: number | null
  topics: string[] | null
  created_at: string
}

export interface TopicGroup {
  topic: string
  messages: MessageItem[]
  emotion_summary: string | null
  message_count: number
  narrative_summary: string | null  // 叙事式摘要（将对话转换为连贯的叙事文本）
}

export interface DailyDetailResponse {
  date: string
  summary_text: string | null
  main_emotion: string | null
  avg_intensity: number | null
  main_topics: string[] | null
  messages: MessageItem[]  // 保留以兼容
  topic_groups: TopicGroup[]  // 新增：按主题分组
}

export interface EmotionStatsOverview {
  trend: Array<{ date: string; score: number }>
  emotion_distribution: Record<string, number>
  top_topics: Array<{ topic: string; count: number }>
}

export interface TokensUsageStats {
  total_prompt_tokens: number
  total_completion_tokens: number
  total_tokens: number
  daily_usage: Array<{
    date: string
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  }>
  message_count: number
}

export interface SessionItem {
  id: string
  title: string | null
  created_at: string
  latest_message_at: string | null
  preview: string | null
}

export interface SessionListResponse {
  sessions: SessionItem[]
}

export interface SessionMessagesResponse {
  session_id: string
  messages: ChatMessage[]
}

// 聊天API
export async function sendChatMessage(
  request: ChatRequest
): Promise<ApiResponse<ChatResponse>> {
  const response = await api.post<ApiResponse<ChatResponse>>('/chat', request)
  return response.data
}

// 获取会话列表
export async function getSessions(): Promise<ApiResponse<SessionListResponse>> {
  const response = await api.get<ApiResponse<SessionListResponse>>('/sessions')
  return response.data
}

// 获取会话消息
export async function getSessionMessages(
  sessionId: string
): Promise<ApiResponse<SessionMessagesResponse>> {
  const response = await api.get<ApiResponse<SessionMessagesResponse>>(
    `/sessions/${sessionId}/messages`
  )
  return response.data
}

// 删除会话
export async function deleteSession(
  sessionId: string
): Promise<ApiResponse<{ success: boolean; message: string }>> {
  const response = await api.delete<ApiResponse<{ success: boolean; message: string }>>(
    `/sessions/${sessionId}`
  )
  return response.data
}

// 生成关心卡
export async function generateCard(
  sessionId: string
): Promise<ApiResponse<ChatResponse>> {
  const response = await api.post<ApiResponse<ChatResponse>>(
    `/sessions/${sessionId}/generate-card`
  )
  return response.data
}

// 日记API
export async function getDailyList(
  from: string,
  to: string
): Promise<ApiResponse<DailyListResponse>> {
  const response = await api.get<ApiResponse<DailyListResponse>>('/daily', {
    params: { from, to },
  })
  return response.data
}

export async function getDailyDetail(
  date: string
): Promise<ApiResponse<DailyDetailResponse>> {
  const response = await api.get<ApiResponse<DailyDetailResponse>>(
    `/daily/${date}`
  )
  return response.data
}

// 统计API
export async function getStatsOverview(
  days: number = 7
): Promise<ApiResponse<EmotionStatsOverview>> {
  const response = await api.get<ApiResponse<EmotionStatsOverview>>(
    '/stats/overview',
    {
      params: { days },
    }
  )
  return response.data
}

export async function getTokensStats(
  days: number = 30
): Promise<ApiResponse<TokensUsageStats>> {
  const response = await api.get<ApiResponse<TokensUsageStats>>(
    '/stats/tokens',
    {
      params: { days },
    }
  )
  return response.data
}

// AI配置相关接口
export interface AIConfig {
  id: string
  provider: string
  is_active: boolean
  api_key: string | null
  base_url: string | null
  model: string | null
  extra_config: Record<string, any> | null
  created_at: string
  updated_at: string
}

export interface AIConfigListResponse {
  configs: AIConfig[]
  active_provider: string | null
}

export interface AIConfigCreate {
  provider: string
  api_key?: string | null
  base_url?: string | null
  model?: string | null
  extra_config?: Record<string, any> | null
}

export interface AIConfigUpdate {
  api_key?: string | null
  base_url?: string | null
  model?: string | null
  extra_config?: Record<string, any> | null
  is_active?: boolean
}

// 获取所有AI配置
export async function getAIConfigs(): Promise<ApiResponse<AIConfigListResponse>> {
  const response = await api.get<ApiResponse<AIConfigListResponse>>('/ai-config')
  return response.data
}

// 创建AI配置
export async function createAIConfig(
  config: AIConfigCreate
): Promise<ApiResponse<AIConfig>> {
  const response = await api.post<ApiResponse<AIConfig>>('/ai-config', config)
  return response.data
}

// 更新AI配置
export async function updateAIConfig(
  provider: string,
  config: AIConfigUpdate
): Promise<ApiResponse<AIConfig>> {
  const response = await api.put<ApiResponse<AIConfig>>(
    `/ai-config/${provider}`,
    config
  )
  return response.data
}

// 激活AI配置
export async function activateAIConfig(
  provider: string
): Promise<ApiResponse<AIConfig>> {
  const response = await api.post<ApiResponse<AIConfig>>(
    `/ai-config/${provider}/activate`
  )
  return response.data
}