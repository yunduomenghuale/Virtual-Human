import { http } from './http'

export interface ChatSession {
  id: string
  title: string
  messages: any[]
  user_name?: string
  user_real_name?: string
  message_count?: number
  created_at: string
  updated_at: string
}

export const chatApi = {
  list: () =>
    http.get<unknown, { results: ChatSession[]; count: number }>('/agent/sessions/'),

  retrieve: (id: string) =>
    http.get<unknown, ChatSession>(`/agent/sessions/${id}/`),

  create: (data: Partial<ChatSession>) =>
    http.post<unknown, ChatSession>('/agent/sessions/', data),

  update: (id: string, data: Partial<ChatSession>) =>
    http.put<unknown, ChatSession>(`/agent/sessions/${id}/`, data),

  remove: (id: string) =>
    http.delete(`/agent/sessions/${id}/`),
}
