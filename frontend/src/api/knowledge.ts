import { http } from './http'
import type { QAResult } from '@/types'

export const knowledgeApi = {
  ask: (question: string, top_k = 4) =>
    http.post<unknown, QAResult>('/knowledge/ask/', { question, top_k }),

  /** 流式问答:逐 token 回调 */
  askStream: async (question: string, top_k = 4, onToken: (text: string) => void) => {
    const token = localStorage.getItem('access_token') || ''
    const resp = await fetch('/api/knowledge/ask/stream/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ question, top_k }),
    })
    if (!resp.ok) {
      const err = await resp.text()
      throw new Error(err)
    }
    const reader = resp.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''
      for (const part of parts) {
        const dataLine = part.split('\n').find(l => l.startsWith('data: '))
        if (!dataLine) continue
        const data = dataLine.slice(6)
        try {
          const parsed = JSON.parse(data)
          if (parsed.type === 'token') onToken(parsed.text)
        } catch { /* ignore parse error */ }
      }
    }
  },

  sessionList: (params?: any) =>
    http.get<unknown, { results: QAResult[]; count: number }>('/knowledge/sessions/', { params }),

  documentList: () =>
    http.get<unknown, { results: any[]; count: number }>('/knowledge/documents/'),

  ingestText: (data: { source: string; title: string; text: string; description?: string }) =>
    http.post('/knowledge/documents/ingest_text/', data),

  ingestFile: (file: File, title: string, description = '') => {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('title', title)
    fd.append('description', description)
    return http.post('/knowledge/documents/ingest_file/', fd)
  },

  removeDocument: (id: number) => http.delete(`/knowledge/documents/${id}/`),
  reloadCorpus: () => http.post('/knowledge/documents/reload_corpus/'),
}
