<template>
  <div class="agent-page">
    <!-- toolbar -->
    <div class="agent-toolbar">
      <el-button text class="new-chat-btn" @click="newChat">
        <el-icon :size="16"><Plus /></el-icon>
        <span>新对话</span>
      </el-button>
      <div class="toolbar-title">消防安全小安</div>
      <div style="width: 90px;"></div>
    </div>

    <!-- messages -->
    <div ref="scrollerRef" class="msg-list">
      <!-- empty state -->
      <div v-if="!messages.length" class="empty-state">
        <h1>有什么我能帮你的吗？</h1>
        <div class="skill-row">
          <el-tag v-for="s in skills" :key="s.code"
                  :type="auth.hasSkill(s.code as any) ? 'success' : 'info'"
                  :effect="auth.hasSkill(s.code as any) ? 'light' : 'plain'"
                  round size="small">
            <el-icon style="margin-right:4px"><component :is="s.icon" /></el-icon>{{ s.label }}
          </el-tag>
        </div>
        <div class="suggestion-pills">
          <el-button v-for="ex in EXAMPLES" :key="ex"
                     round class="pill"
                     @click="useExample(ex, false)">{{ ex }}</el-button>
        </div>
      </div>

      <!-- messages -->
      <template v-for="(m, idx) in messages" :key="idx">
        <div v-if="m.role === 'user'" class="msg msg-user">
          <div class="bubble bubble-user" :class="{ 'bubble-user-plain': !m.content && (m.attachmentUrl || m.attachmentBase64) }">
            <img v-if="m.attachmentBase64 || m.attachmentUrl" :src="m.attachmentBase64 || m.attachmentUrl" class="bubble-img" />
            <div v-if="m.content" class="bubble-text">{{ m.content }}</div>
          </div>
        </div>
        <div v-else-if="m.content || (m.toolCalls || []).length || m.pending || idx === typingIdx" class="msg msg-bot">
          <div class="bubble bubble-bot">
            <div v-for="(tc, i) in (m.toolCalls || []).filter(t => t.result?.type !== 'knowledge_qa' && t.ok !== false)" :key="i" class="tool-card-wrap">
              <ToolCard :tc="tc" />
            </div>
            <div v-if="m.pending || (idx === typingIdx && !typingText)" class="typing"><span /><span /><span /></div>
            <MarkdownText v-if="idx === typingIdx ? typingText : m.content" :text="idx === typingIdx ? typingText : m.content" />
          </div>
        </div>
      </template>
    </div>

    <!-- composer -->
    <div class="composer">
      <div class="composer-box">
        <div v-if="pendingImage" class="attach-preview">
          <img :src="pendingImageUrl" />
          <el-button size="small" circle class="attach-remove" @click="clearImage">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
        <el-input v-model="input" type="textarea" :rows="2" resize="none"
                  placeholder="发消息..."
                  class="composer-input"
                  @keydown="onKeydown" />
        <div class="composer-footer">
          <div class="quick-actions">
            <el-upload :auto-upload="false" :show-file-list="false"
                       :on-change="onPick" accept="image/png,image/jpeg">
              <el-button text size="small" :disabled="!canUseHazard" title="上传图片"
                         class="attach-btn">
                <el-icon :size="18"><Plus /></el-icon>
              </el-button>
            </el-upload>
            <span class="action-divider" />
          </div>
          <el-button type="primary" :disabled="!canSend" :loading="loading"
                     circle class="send-btn" @click="send">
            <el-icon v-if="!loading"><ArrowUpBold /></el-icon>
          </el-button>
        </div>
      </div>
      <div class="composer-hint">内容由 AI 生成，请仔细甄别</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { agentApi } from '@/api/agent'
import { knowledgeApi } from '@/api/knowledge'
import { chatApi } from '@/api/chat'
import type { AgentMessage, Skill } from '@/types'
import ToolCard from './agent/ToolCard.vue'
import MarkdownText from '@/components/MarkdownText.vue'

const auth = useAuthStore()

const messages = ref<AgentMessage[]>([])
const input = ref('')
const pendingImage = ref<File | null>(null)
const pendingImageUrl = ref('')
const pendingImageBase64 = ref('')
const loading = ref(false)
const scrollerRef = ref<HTMLElement>()
const isTyping = ref(false)
const typingIdx = ref<number>(-1)
const typingText = ref('')
let typingRunId = 0
const currentSessionId = ref<string | null>(null)
const directKnowledgeMode = ref(false)

async function compressImageFile(file: File, maxWidth = 1200, quality = 0.8): Promise<File> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => {
      const scale = Math.min(1, maxWidth / img.width)
      const canvas = document.createElement('canvas')
      canvas.width = Math.round(img.width * scale)
      canvas.height = Math.round(img.height * scale)
      const ctx = canvas.getContext('2d')!
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
      canvas.toBlob((blob) => {
        if (blob) {
          resolve(new File([blob], file.name, { type: 'image/jpeg' }))
        } else {
          reject(new Error('压缩失败'))
        }
        URL.revokeObjectURL(img.src)
      }, 'image/jpeg', quality)
    }
    img.onerror = () => {
      URL.revokeObjectURL(img.src)
      reject(new Error('图片加载失败'))
    }
    img.src = URL.createObjectURL(file)
  })
}

async function compressImageToBase64(file: File, maxWidth = 800, quality = 0.7): Promise<string> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => {
      const scale = Math.min(1, maxWidth / img.width)
      const canvas = document.createElement('canvas')
      canvas.width = Math.round(img.width * scale)
      canvas.height = Math.round(img.height * scale)
      const ctx = canvas.getContext('2d')!
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
      resolve(canvas.toDataURL('image/jpeg', quality))
      URL.revokeObjectURL(img.src)
    }
    img.onerror = () => {
      URL.revokeObjectURL(img.src)
      reject(new Error('图片加载失败'))
    }
    img.src = URL.createObjectURL(file)
  })
}

function getSessionTitle(): string {
  const firstUser = messages.value.find(m => m.role === 'user')
  return firstUser?.content?.slice(0, 24) || '新对话'
}

async function saveCurrentSession() {
  if (!messages.value.length) return
  const payload = {
    title: getSessionTitle(),
    messages: messages.value.map((m, i) => ({
      role: m.role,
      content: (i === typingIdx.value && typingText.value) ? typingText.value : m.content,
      attachmentBase64: m.attachmentBase64,
      toolCalls: m.toolCalls,
    })),
  }
  if (!currentSessionId.value) {
    const created = await chatApi.create(payload)
    currentSessionId.value = created.id
  } else {
    await chatApi.update(currentSessionId.value, payload)
  }
}

async function restoreSession(id: string) {
  try {
    const s = await chatApi.retrieve(id)
    currentSessionId.value = id
    messages.value = (s.messages || []).map((m: any) => ({
      ...m,
      attachmentUrl: m.attachmentBase64 || undefined,
    }))
    return true
  } catch {
    return false
  }
}

const skills: { code: Skill; label: string; icon: string }[] = [
  { code: 'knowledge_qa',  label: '知识问答', icon: 'ChatLineSquare' },
  { code: 'hazard_detect', label: '隐患识别', icon: 'Picture' },
  { code: 'report_gen',    label: '报告生成', icon: 'Document' },
  { code: 'analytics',     label: '数据分析', icon: 'DataAnalysis' },
]

const canUseHazard = computed(() => auth.hasSkill('hazard_detect'))
const canSend = computed(() =>
  !loading.value && !isTyping.value && (input.value.trim().length > 0 || !!pendingImage.value))

const EXAMPLES = [
  '实验室常见消防隐患有哪些？',
  '查看最近 30 日的检测趋势',
  '总结一下化学楼 305 的隐患情况',
  '帮我生成 化学楼 305 的安全检查报告',
]

function stopTyping() {
  typingRunId++
  isTyping.value = false
  typingIdx.value = -1
  typingText.value = ''
}

async function typeWriter(idx: number, text: string, speed = 30) {
  const runId = ++typingRunId
  isTyping.value = true
  typingIdx.value = idx
  typingText.value = ''
  for (let i = 0; i < text.length; i += 2) {
    if (runId !== typingRunId) break
    const chunk = text.slice(i, i + 2)
    typingText.value += chunk
    scrollToBottom()
    await new Promise(r => setTimeout(r, speed))
  }
  if (runId === typingRunId) {
    messages.value[idx].content = text
    typingIdx.value = -1
    typingText.value = ''
    isTyping.value = false
    await saveCurrentSession()
    scrollToBottom()
  }
}

async function newChat() {
  stopTyping()
  if (messages.value.length) await saveCurrentSession()
  messages.value = []
  input.value = ''
  clearImage()
  currentSessionId.value = null
}

function useExample(text: string, knowledgeMode = false) {
  input.value = text
  directKnowledgeMode.value = knowledgeMode
}

async function onPick(f: any) {
  const real = f.raw || f
  if (!real) return
  if (!canUseHazard.value) {
    ElMessage.warning('当前角色未启用「隐患识别」skill')
    return
  }
  if (pendingImageUrl.value) URL.revokeObjectURL(pendingImageUrl.value)
  // 压缩后上传(最大1200px,减少视觉模型推理时间)
  try {
    pendingImage.value = await compressImageFile(real, 1200, 0.8)
  } catch {
    pendingImage.value = real
  }
  pendingImageUrl.value = URL.createObjectURL(pendingImage.value)
  try {
    pendingImageBase64.value = await compressImageToBase64(pendingImage.value, 800, 0.7)
  } catch {
    pendingImageBase64.value = ''
  }
}

function clearImage() {
  if (pendingImageUrl.value) URL.revokeObjectURL(pendingImageUrl.value)
  pendingImage.value = null
  pendingImageUrl.value = ''
  pendingImageBase64.value = ''
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
    e.preventDefault()
    if (canSend.value) send()
  }
}

async function send() {
  if (!canSend.value) return
  stopTyping()
  const userMsg: AgentMessage = {
    role: 'user',
    content: input.value.trim() || '',
    attachmentUrl: pendingImageUrl.value || undefined,
    attachmentBase64: pendingImageBase64.value || undefined,
  }
  messages.value.push(userMsg)
  const placeholderIdx = messages.value.length
  messages.value.push({ role: 'assistant', content: '', pending: true })
  scrollToBottom()

  const sentImage = pendingImage.value
  const sentImageUrl = pendingImageUrl.value
  const userContent = input.value.trim()
  input.value = ''
  pendingImage.value = null
  pendingImageUrl.value = ''
  pendingImageBase64.value = ''
  loading.value = true

  // 快速路径:直接知识库问答(无图片且标记了知识问答模式)
  const useDirectQA = directKnowledgeMode.value && !sentImage
  directKnowledgeMode.value = false // 用完重置

  try {
    if (useDirectQA) {
      messages.value[placeholderIdx].content = ''
      let firstToken = true
      await knowledgeApi.askStream(userContent, 4, (token) => {
        if (firstToken) {
          messages.value[placeholderIdx].pending = false
          firstToken = false
        }
        messages.value[placeholderIdx].content += token
        scrollToBottom()
      })
      messages.value[placeholderIdx].pending = false
      await saveCurrentSession()
    } else {
      const res = await agentApi.chat(
        messages.value.filter((_, i) => i !== placeholderIdx),
        sentImage,
      )
      messages.value[placeholderIdx].pending = false
      messages.value[placeholderIdx].toolCalls = res.tool_calls
      typeWriter(placeholderIdx, res.message || '')
    }
  } catch (e: any) {
    messages.value[placeholderIdx].pending = false
    const detail = e?.response?.data?.detail || e?.message || ''
    messages.value[placeholderIdx].content = detail ? `抱歉，出错了：${detail}` : '抱歉，刚刚出错了。'
  } finally {
    loading.value = false
    if (sentImageUrl && !messages.value.some(m => m.attachmentUrl === sentImageUrl)) {
      URL.revokeObjectURL(sentImageUrl)
    }
    await saveCurrentSession()
    scrollToBottom()
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (scrollerRef.value) {
      scrollerRef.value.scrollTop = scrollerRef.value.scrollHeight
    }
  })
}

onMounted(async () => {
  if (!auth.user) await auth.fetchMe()
  const sid = new URLSearchParams(window.location.search).get('session')
  if (sid) {
    const ok = await restoreSession(sid)
    if (!ok) currentSessionId.value = null
  } else {
    currentSessionId.value = null
  }
})
</script>

<style scoped>
.agent-page {
  height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
  background: #fff;
  max-width: 1500px;
  margin: 0 auto;
  border-radius: 12px;
}

/* toolbar */
.agent-toolbar {
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 22px;
  border-bottom: 1px solid #f0f0f0;
  flex-shrink: 0;
}
.new-chat-btn {
  font-size: 13px;
  color: var(--txt-secondary);
}
.toolbar-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--txt-primary);
}

/* msg list */
.msg-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px 0;
}

/* empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 50vh;
  gap: 18px;
}
.empty-state h1 {
  font-size: 28px;
  font-weight: 700;
  color: var(--txt-primary);
  margin: 0;
  letter-spacing: 0.5px;
}
.skill-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
}
.suggestion-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
  max-width: 720px;
  margin-top: 8px;
}
.pill {
  border-radius: 999px !important;
  padding: 8px 16px !important;
  font-size: 13px;
  color: var(--txt-secondary);
  background: #f5f5f5;
  border: 1px solid #eee;
  transition: all .2s ease;
}
.pill:hover {
  background: #eee;
  border-color: #ddd;
  color: var(--txt-primary);
}

/* messages */
.msg {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 0;
  margin: 0 auto 24px;
  max-width: 720px;
}
.msg-user {
  justify-content: flex-end;
}
.msg-bot {
  justify-content: flex-start;
}
.avatar {
  flex-shrink: 0;
}
.avatar-bot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--grad-brand);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  margin-top: 4px;
}

.bubble {
  word-wrap: break-word;
}
.bubble-user {
  background: linear-gradient(135deg, #ff7a1a 0%, #d62828 100%);
  color: #fff;
  border-radius: 18px;
  border-bottom-right-radius: 4px;
  padding: 10px 16px;
  max-width: 70%;
  font-size: 15px;
  line-height: 1.7;
  box-shadow: 0 1px 2px rgba(15,23,42,.04);
}
.bubble-bot {
  background: transparent;
  color: var(--txt-primary);
  padding: 4px 0;
  max-width: 100%;
  font-size: 15px;
  line-height: 1.8;
}
.bubble-img {
  display: block;
  max-width: 280px;
  max-height: 200px;
  border-radius: 8px;
  margin-bottom: 6px;
}
.bubble-user .bubble-img { box-shadow: 0 4px 12px rgba(0,0,0,.15); }
.bubble-user-plain {
  background: transparent !important;
  padding: 0 !important;
  box-shadow: none !important;
  border-radius: 12px;
  overflow: hidden;
}
.bubble-user-plain .bubble-img {
  margin-bottom: 0;
  box-shadow: none;
  border-radius: 12px;
  max-width: 260px;
  max-height: 360px;
}
.tool-card-wrap + .tool-card-wrap { margin-top: 10px; }
.tool-card-wrap { margin-bottom: 10px; }

.typing {
  display: inline-flex;
  gap: 4px;
  padding: 8px 0;
}
.typing span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--brand-orange);
  animation: typing 1.4s infinite both;
}
.typing span:nth-child(2) { animation-delay: .2s; }
.typing span:nth-child(3) { animation-delay: .4s; }
@keyframes typing {
  0%, 60%, 100% { opacity: .25; transform: translateY(0); }
  30% { opacity: 1; transform: translateY(-3px); }
}

/* composer */
.composer {
  padding: 8px 22px 16px;
  flex-shrink: 0;
  background: #fff;
}
.composer-box {
  max-width: 720px;
  margin: 0 auto;
  border: 1px solid #e5e7eb;
  border-radius: 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,.06);
  padding: 12px 16px;
  transition: box-shadow .2s ease, border-color .2s ease;
}
.composer-box:focus-within {
  box-shadow: 0 4px 20px rgba(0,0,0,.08);
  border-color: #d1d5db;
}
.attach-preview {
  position: relative;
  display: inline-block;
  margin-bottom: 8px;
}
.attach-preview img {
  max-width: 120px;
  max-height: 90px;
  border-radius: 8px;
  border: 1px solid var(--line-soft);
}
.attach-remove {
  position: absolute;
  top: -8px;
  right: -8px;
  background: #fff !important;
  border: 1px solid var(--line) !important;
  color: var(--txt-secondary) !important;
}
.composer-input :deep(.el-textarea__inner) {
  border: none !important;
  background: transparent !important;
  box-shadow: none !important;
  padding: 4px 0;
  resize: none;
  font-size: 14px;
  line-height: 1.6;
}
.composer-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
}
.quick-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.attach-btn {
  color: var(--txt-secondary) !important;
  padding: 4px !important;
}
.attach-btn:hover {
  color: var(--txt-primary) !important;
  background: transparent !important;
}
.action-divider {
  width: 1px;
  height: 16px;
  background: #e5e7eb;
  display: inline-block;
}
.send-btn {
  width: 32px !important;
  height: 32px !important;
  padding: 0 !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
}
.composer-hint {
  text-align: center;
  font-size: 11px;
  color: var(--txt-muted);
  margin-top: 8px;
}
</style>
