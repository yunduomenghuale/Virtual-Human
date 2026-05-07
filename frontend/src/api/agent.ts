import { http } from './http'
import type { AgentChatResponse, AgentMessage, Skill } from '@/types'

export const agentApi = {
  /**
   * 与 agent 对话。
   * @param messages 历史消息(只发送 role + content,attachment / pending 等前端字段会被剥离)
   * @param attachment 可选图片附件,会触发 hazard_detect 工具
   */
  chat: (messages: AgentMessage[], attachment?: File | null) => {
    const safeMessages = messages
      .filter(m => m.role === 'user' || m.role === 'assistant')
      .map(m => ({ role: m.role, content: m.content }))
    const fd = new FormData()
    fd.append('messages', JSON.stringify(safeMessages))
    if (attachment) fd.append('attachment', attachment)
    return http.post<unknown, AgentChatResponse>('/agent/chat/', fd)
  },

  skills: () =>
    http.get<unknown, { enabled_skills: Skill[] }>('/agent/skills/'),

  asr: (audioBlob: Blob) => {
    const fd = new FormData()
    fd.append('audio', audioBlob, 'recording.webm')
    return http.post<unknown, { text: string }>('/agent/asr/', fd)
  },
}
