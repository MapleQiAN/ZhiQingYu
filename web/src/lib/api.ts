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
  emotion_echo?: string
  clarification?: string
  suggestion?: string[] | string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  card_data?: CardData | null
}

export interface ChatRequest {
  session_id?: string | null
  messages: ChatMessage[]
}

export interface ChatResponse {
  session_id: string
  reply: string
  emotion: string
  intensity: number
  topics: string[]
  risk_level: 'normal' | 'high'
  card_data?: CardData | null
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

export interface DailyDetailResponse {
  date: string
  summary_text: string | null
  main_emotion: string | null
  avg_intensity: number | null
  main_topics: string[] | null
  messages: MessageItem[]
}

export interface EmotionStatsOverview {
  trend: Array<{ date: string; score: number }>
  emotion_distribution: Record<string, number>
  top_topics: Array<{ topic: string; count: number }>
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