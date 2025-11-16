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

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
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

// 聊天API
export async function sendChatMessage(
  request: ChatRequest
): Promise<ApiResponse<ChatResponse>> {
  const response = await api.post<ApiResponse<ChatResponse>>('/chat', request)
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
