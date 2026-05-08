import { http } from './http'
import type { AgentChatResponse, AgentMessage, Skill } from '@/types'

export const agentApi = {
  /**
   * 与 agent 对话。
   * @param messages 历史消息(只发送 role + content,attachment / pending 等前端字段会被剥离)
   * @param attachments 可选图片附件,会触发 hazard_detect 工具
   */
  chat: (messages: AgentMessage[], attachments?: File[] | File | null) => {
    const safeMessages = messages
      .filter(m => m.role === 'user' || m.role === 'assistant')
      .map(m => ({ role: m.role, content: m.content }))
    const fd = new FormData()
    fd.append('messages', JSON.stringify(safeMessages))
    const files = Array.isArray(attachments) ? attachments : (attachments ? [attachments] : [])
    files.forEach(file => fd.append(file.type.startsWith('video/') ? 'videos' : 'attachments', file))
    return http.post<unknown, AgentChatResponse>('/agent/chat/', fd)
  },

  skills: () =>
    http.get<unknown, { enabled_skills: Skill[] }>('/agent/skills/'),
}
