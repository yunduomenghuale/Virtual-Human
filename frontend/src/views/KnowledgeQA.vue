<template>
  <div class="page">
    <el-card class="qa-card">
      <div class="messages" ref="msgsEl">
        <div v-if="!messages.length" class="empty">
          <div class="empty-icon">
            <el-icon :size="36" color="#ff7a1a"><ChatRound /></el-icon>
          </div>
          <p style="margin: 4px 0 0;">问点什么吧 — 试试这些常见问题:</p>
          <div class="suggest">
            <el-tag v-for="s in suggestions" :key="s" effect="plain" round
                    @click="quickAsk(s)">{{ s }}</el-tag>
          </div>
        </div>
        <div v-for="(m, idx) in messages" :key="idx" :class="['msg', m.role]">
          <span class="avatar" :class="m.role === 'user' ? 'user-av' : 'bot-av'">
            <el-icon :size="18"><component :is="m.role === 'user' ? 'User' : 'Star'" /></el-icon>
          </span>
          <div class="bubble">
            <div class="bubble-text" v-html="renderMd(m.content)"></div>
            <div v-if="m.sources?.length" class="sources">
              <div class="muted" style="margin-bottom:4px;">参考依据:</div>
              <el-tag v-for="(s, i) in m.sources" :key="i" size="small" effect="plain"
                      style="margin-right: 6px; margin-bottom: 4px;">
                {{ s.title }} ({{ s.score }})
              </el-tag>
            </div>
          </div>
        </div>
      </div>

      <div class="composer">
        <el-input v-model="input" type="textarea" :rows="3" placeholder="输入问题,Ctrl+Enter 发送"
                  @keydown.ctrl.enter="ask" :disabled="loading" />
        <div style="margin-top:8px; display:flex; gap:10px;">
          <el-input-number v-model="topK" :min="1" :max="10" size="small" />
          <span class="muted" style="line-height: 24px;">检索片段数</span>
          <el-button type="primary" :loading="loading" @click="ask" style="margin-left:auto;">
            发送
          </el-button>
          <el-button v-if="messages.length" plain @click="messages = []">清空</el-button>
        </div>
      </div>
    </el-card>

    <el-card style="margin-top: 14px;">
      <template #header><span class="section-title" style="margin:0;">历史问答</span></template>
      <el-table :data="history" size="small" empty-text="暂无记录">
        <el-table-column prop="created_at" label="时间" width="170" />
        <el-table-column prop="question" label="问题" show-overflow-tooltip />
        <el-table-column prop="answer" label="回答" show-overflow-tooltip />
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button link @click="replay(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { knowledgeApi } from '@/api/knowledge'
import type { QAResult } from '@/types'

interface ChatMessage { role: 'user' | 'assistant'; content: string; sources?: { title: string; snippet: string; score: number }[] }
const messages = ref<ChatMessage[]>([])
const history = ref<QAResult[]>([])
const input = ref('')
const topK = ref(4)
const loading = ref(false)
const msgsEl = ref<HTMLElement | null>(null)
const suggestions = [
  '灭火器多久年检一次?',
  '化学品柜的存放规范有哪些?',
  '实验室用电安全注意事项',
  '发生火灾时应如何疏散?',
]

function quickAsk(q: string) {
  input.value = q
  ask()
}

async function ask() {
  const q = input.value.trim()
  if (!q || loading.value) return
  messages.value.push({ role: 'user', content: q })
  input.value = ''
  loading.value = true
  try {
    const resp = await knowledgeApi.ask(q, topK.value)
    messages.value.push({ role: 'assistant', content: resp.answer, sources: resp.sources })
    fetchHistory()
  } finally {
    loading.value = false
    await nextTick()
    msgsEl.value?.scrollTo({ top: msgsEl.value.scrollHeight, behavior: 'smooth' })
  }
}

function replay(row: QAResult) {
  messages.value = [
    { role: 'user', content: row.question },
    { role: 'assistant', content: row.answer, sources: row.sources },
  ]
}

async function fetchHistory() {
  try {
    const r = await knowledgeApi.sessionList({ page_size: 20 })
    history.value = r.results || []
  } catch {}
}

function renderMd(text: string) {
  return (text || '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\n/g, '<br/>')
    .replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
}

onMounted(fetchHistory)
</script>

<style scoped>
.qa-card { display: flex; flex-direction: column; }
.qa-card :deep(.el-card__body) { display: flex; flex-direction: column; gap: 14px; padding: 18px !important; }
.messages {
  min-height: 380px; max-height: 540px; overflow: auto;
  background: linear-gradient(180deg, #fafbfc 0%, #f3f5fa 100%);
  padding: 18px; border-radius: 10px;
  border: 1px solid var(--line-soft);
}
.empty {
  text-align: center; padding: 80px 0;
  color: #909399;
  display: flex; flex-direction: column; align-items: center; gap: 10px;
}
.empty .empty-icon {
  width: 76px; height: 76px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, rgba(255,122,26,.15), rgba(214,40,40,.12));
}
.empty .suggest {
  display: flex; gap: 8px; flex-wrap: wrap; justify-content: center;
  margin-top: 6px;
}
.empty .suggest .el-tag { cursor: pointer; }

.msg { display: flex; gap: 10px; margin-bottom: 16px; align-items: flex-start; }
.msg.user { flex-direction: row-reverse; }
.avatar {
  flex-shrink: 0;
  width: 36px; height: 36px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: #fff;
  box-shadow: 0 4px 10px rgba(0,0,0,.08);
}
.avatar.user-av { background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%); }
.avatar.bot-av  { background: linear-gradient(135deg, #ff7a1a 0%, #d62828 100%); }

.bubble {
  max-width: 72%;
  padding: 12px 16px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #ebeef5;
  line-height: 1.75;
  box-shadow: 0 2px 8px rgba(15,23,42,.04);
}
.msg.user .bubble {
  background: linear-gradient(135deg, #ecf5ff 0%, #dbeafe 100%);
  border-color: #d9ecff;
}
.bubble-text { color: var(--txt-primary); }
.sources {
  margin-top: 10px; padding-top: 10px; border-top: 1px dashed #ebeef5;
}
.composer { padding-top: 6px; }
.composer :deep(.el-textarea__inner) {
  border-radius: 10px !important;
  resize: none;
}
.history-card { margin-top: 14px; }
</style>
