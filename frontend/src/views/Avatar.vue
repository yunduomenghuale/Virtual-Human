<template>
  <div class="avatar-page" :class="{ fullscreen: isFullscreen }">
    <!-- header -->
    <div class="avatar-header">
      <el-button v-if="!isFullscreen" text @click="$router.push('/agent')">
        <el-icon><ArrowLeft /></el-icon>
        <span>返回小安</span>
      </el-button>
      <div v-else style="width: 90px;" />
      <div class="header-center">
        <span class="status-dot" :class="avatarState" />
        <span class="status-text">{{ stateLabel }}</span>
      </div>
      <div style="width: 90px;" />
    </div>

    <!-- 数字人渲染区 -->
    <div class="avatar-stage">
      <div id="avatar-container" class="avatar-container" />
      <div v-if="!sdkReady" class="avatar-placeholder">
        <el-icon :size="48" color="#ddd"><VideoCamera /></el-icon>
        <p class="muted">数字人加载中...</p>
        <p v-if="sdkError" class="error-text">{{ sdkError }}</p>
      </div>
      <!-- AI 思考提示 -->
      <div v-if="aiLoading" class="thinking-bubble">
        <div class="typing"><span /><span /><span /></div>
        <span class="thinking-text">小安正在思考...</span>
      </div>

      <!-- 场景演练内容面板 -->
      <div v-if="scenarioCall" class="scenario-panel">
        <!-- 场景列表 -->
        <div v-if="scenarioCall.result.mode === 'list'" class="sp-list">
          <div class="sp-head">
            <span class="sp-icon">📚</span>
            <span class="sp-title">消防培训场景库</span>
            <span class="sp-count">共 {{ (scenarioCall.result as any).items.length }} 个</span>
          </div>
          <div class="sp-list-body">
            <div
              v-for="item in (scenarioCall.result as any).items"
              :key="item.id"
              class="sp-item"
              @click="selectScenario(item.title)"
            >
              <div class="sp-item-main">
                <div class="sp-item-title">{{ item.title }}</div>
                <div class="sp-item-meta">
                  <span class="sp-tag">{{ item.topic }}</span>
                  <span class="sp-tag" :class="'diff-' + item.difficulty">{{ item.difficulty }}</span>
                </div>
                <div class="sp-item-desc">{{ item.description }}</div>
              </div>
              <el-button type="primary" size="small" plain>选择</el-button>
            </div>
          </div>
          <div class="sp-tip">点击场景即可开始学习，或直接对数字人说出场景名称</div>
        </div>

        <!-- 教学模式 -->
        <div v-else-if="scenarioCall.result.mode === 'teaching'" class="sp-teaching">
          <div class="sp-head">
            <span class="sp-icon">📖</span>
            <span class="sp-title">{{ (scenarioCall.result as any).data.title }}</span>
          </div>
          <div class="sp-content">
            <MarkdownText :text="(scenarioCall.result as any).data.teaching_content || '暂无讲义内容'" />
          </div>
          <div class="sp-tip">讲解完毕后，请对小安说"开始实战测试"</div>
        </div>

        <!-- 演习模式 - 评分结果 -->
        <div v-else-if="scenarioCall.result.mode === 'testing' && (scenarioCall.result as any).score != null" class="sp-result">
          <div class="sp-result-header">
            <div class="sp-result-label">演练评估结果</div>
            <div class="sp-score" :class="((scenarioCall.result as any).score || 0) >= 80 ? 'good' : ((scenarioCall.result as any).score || 0) >= 60 ? 'pass' : 'fail'">
              {{ (scenarioCall.result as any).score }}<span>分</span>
            </div>
          </div>
          <div class="sp-analysis">
            <div class="sp-analysis-title">专家点评</div>
            <div class="sp-analysis-body">
              <MarkdownText :text="(scenarioCall.result as any).analysis || '暂无点评'" />
            </div>
          </div>
        </div>

        <!-- 演习模式 - 首次进入 -->
        <div v-else-if="scenarioCall.result.mode === 'testing'" class="sp-testing">
          <div class="sp-head">
            <span class="sp-icon">🎯</span>
            <span class="sp-title">{{ (scenarioCall.result as any).data.title }}</span>
            <span class="sp-tag" :class="'diff-' + (scenarioCall.result as any).data.difficulty">{{ (scenarioCall.result as any).data.difficulty }}</span>
          </div>
          <div v-if="(scenarioCall.result as any).data.image" class="sp-image">
            <img :src="(scenarioCall.result as any).data.image" />
          </div>
          <div class="sp-desc">
            <MarkdownText :text="(scenarioCall.result as any).data.description" />
          </div>
        </div>
      </div>

      <!-- 最近一条 AI 回复（Markdown 渲染） -->
      <div v-else-if="lastAiMsg" class="ai-msg-bubble">
        <MarkdownText class="ai-msg-md" :text="lastAiMsg" inline />
      </div>
    </div>

    <!-- 底部控制区 -->
    <div class="avatar-controls">
      <div class="composer-glass">
        <div class="composer-main">
          <div v-if="pendingImages.length" class="attach-preview-list">
            <div v-for="(item, idx) in pendingImages" :key="item.key" class="attach-preview">
              <img v-if="item.url" :src="item.url" />
              <div v-else class="attach-video">{{ item.name }}</div>
              <el-button size="small" circle class="attach-remove" @click="removeImage(idx)">
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
          </div>

          <!-- 录音状态栏 -->
          <div v-if="isRecording" class="recording-bar">
            <div class="recording-wave">
              <span v-for="n in 5" :key="n" :style="{ animationDelay: (n * 0.1) + 's' }" />
            </div>
            <span class="recording-text">正在聆听，点击麦克风结束</span>
            <div class="recording-timer">{{ recordingDuration }}s</div>
          </div>

          <el-input
            v-model="inputText"
            type="textarea"
            :rows="2"
            placeholder="输入文字让小安说话..."
            resize="none"
            class="text-input"
            @keydown="onKeydown"
          />
          <div class="composer-tools">
            <el-upload
              multiple
              :auto-upload="false"
              :show-file-list="false"
              :on-change="onPick"
              accept="image/png,image/jpeg,video/mp4,video/webm,video/quicktime"
            >
              <el-button
                text
                size="small"
                :disabled="!canUseHazard"
                class="attach-btn"
              >
                <el-icon :size="18"><Plus /></el-icon>
              </el-button>
            </el-upload>
            <el-button
              text
              size="small"
              :disabled="!canUseHazard"
              class="attach-btn"
              @click="cameraVisible = true"
            >
              <el-icon :size="18"><Camera /></el-icon>
            </el-button>
            <div class="mic-wrap">
              <div v-if="isRecording" class="mic-ripple" />
              <el-button
                text
                size="small"
                :class="['attach-btn', 'mic-btn', { recording: isRecording }]"
                :title="isRecording ? '点击结束录音' : '语音输入'"
                @click="toggleRecording"
              >
                <el-icon :size="18"><Microphone /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
        <div class="control-btns">
          <el-button
            type="primary"
            :disabled="!canSpeak"
            circle
            size="large"
            class="send-btn"
            @click="speakText"
          >
            <el-icon :size="20"><Promotion /></el-icon>
          </el-button>
        </div>
      </div>
    </div>
    <CameraCapture v-model="cameraVisible" @capture="addPendingImage" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { agentApi } from '@/api/agent'
import type { AgentMessage } from '@/types'
import CameraCapture from '@/components/CameraCapture.vue'
import { extractVideoCover } from '@/utils/videoCover'
import MarkdownText from '@/components/MarkdownText.vue'
import type { AgentMessage, AgentToolCall } from '@/types'

const route = useRoute()
const auth = useAuthStore()
const isFullscreen = computed(() => route.path === '/avatar-live')

const avatarState = ref<'idle' | 'listen' | 'think' | 'speak'>('idle')
const sdkReady = ref(false)
const sdkError = ref('')
const inputText = ref('')
const isRecording = ref(false)
const recordingDuration = ref(0)
let finalTranscript = ''
let recordingTimer: number | null = null
const aiLoading = ref(false)
const messages = ref<AgentMessage[]>([])
const pendingImages = ref<{ file: File; url: string; base64: string; name: string; key: string }[]>([])
const cameraVisible = ref(false)

let avatar: any = null
let recognition: any = null

const stateLabel = computed(() => {
  const map: Record<string, string> = {
    idle: '待机中',
    listen: '倾听中...',
    think: '思考中...',
    speak: '说话中...',
  }
  return map[avatarState.value] || '待机中'
})

const canUseHazard = computed(() => auth.hasSkill('hazard_detect'))
const canSpeak = computed(() =>
  sdkReady.value && !aiLoading.value && (inputText.value.trim().length > 0 || pendingImages.value.length > 0))

const lastAiMsg = computed(() => {
  const last = [...messages.value].reverse().find(m => m.role === 'assistant')
  return last?.content || ''
})

/** 当前会话中的场景演练 toolCall */
const scenarioCall = computed((): any => {
  const last = [...messages.value].reverse().find(m => m.role === 'assistant')
  if (!last?.toolCalls?.length) return null
  return last.toolCalls.find(
    (tc: AgentToolCall) => tc.result?.type === 'scenario_training' && tc.ok !== false
  ) || null
})

/** 选择场景后自动发送 */
function selectScenario(title: string) {
  inputText.value = `我要学习「${title}」`
  nextTick(() => {
    if (canSpeak.value) speakText()
  })
}

/** 图片压缩 */
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

async function onPick(f: any) {
  const real = (f.raw || f) as File | undefined
  if (!real) return
  if (!canUseHazard.value) {
    ElMessage.warning('当前角色未启用「隐患识别」skill')
    return
  }
  await addPendingImage(real)
}

async function addPendingImage(file: File) {
  if (file.type.startsWith('video/')) {
    let cover = ''
    try {
      cover = await extractVideoCover(file)
    } catch {
      cover = ''
    }
    pendingImages.value.push({
      file,
      url: cover,
      base64: '',
      name: file.name,
      key: `${file.name}-${file.lastModified}-${Date.now()}`,
    })
    ElMessage.success('视频已加入待识别列表')
    return
  }
  try {
    const compressed = await compressImageFile(file, 1200, 0.8)
    await pushPendingImage(compressed, file.name)
  } catch {
    await pushPendingImage(file, file.name)
  }
}

async function pushPendingImage(file: File, originalName: string) {
  const url = URL.createObjectURL(file)
  let base64 = ''
  try {
    base64 = await compressImageToBase64(file, 800, 0.7)
  } catch {
    base64 = ''
  }
  pendingImages.value.push({
    file,
    url,
    base64,
    name: originalName,
    key: `${originalName}-${file.lastModified}-${Date.now()}`,
  })
}

function clearImage() {
  pendingImages.value.forEach(item => URL.revokeObjectURL(item.url))
  pendingImages.value = []
}

function removeImage(index: number) {
  const [removed] = pendingImages.value.splice(index, 1)
  if (removed) URL.revokeObjectURL(removed.url)
}

/** 动态加载魔珐星云 SDK */
function loadSdk(): Promise<void> {
  return new Promise((resolve, reject) => {
    if ((window as any).XmovAvatar) {
      resolve()
      return
    }
    const script = document.createElement('script')
    script.src = 'https://media.xingyun3d.com/xingyun3d/general/litesdk/xmovAvatar@latest.js'
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('SDK 加载失败'))
    document.head.appendChild(script)
  })
}

async function initAvatar() {
  try {
    await loadSdk()
    const XmovAvatar = (window as any).XmovAvatar
    if (!XmovAvatar) {
      throw new Error('SDK 未正确加载')
    }

    // TODO: 替换为你的 AppID 和 AppSecret
    const APP_ID = import.meta.env.VITE_XINGYUN_APP_ID || ''
    const APP_SECRET = import.meta.env.VITE_XINGYUN_APP_SECRET || ''

    if (!APP_ID || !APP_SECRET) {
      sdkError.value = '请在 .env 中配置 VITE_XINGYUN_APP_ID 和 VITE_XINGYUN_APP_SECRET'
      return
    }

    avatar = new XmovAvatar({
      containerId: '#avatar-container',
      appId: APP_ID,
      appSecret: APP_SECRET,
      gatewayServer: 'https://nebula-agent.xingyun3d.com/user/v1/ttsa/session',
      onMessage(msg: any) {
        console.log('[Avatar SDK]', msg)
      },
      onStateChange(state: string) {
        console.log('[Avatar State]', state)
      },
      onVoiceStateChange(status: 'start' | 'end') {
        if (status === 'start') avatarState.value = 'speak'
        if (status === 'end') avatarState.value = 'idle'
      },
    })

    await avatar.init({
      onDownloadProgress: (p: number) => {
        console.log(`加载进度: ${p}%`)
      },
      onError: (err: any) => {
        sdkError.value = String(err)
        console.error('Avatar init error:', err)
      },
    })

    sdkReady.value = true
    avatar.idle()
  } catch (e: any) {
    sdkError.value = e?.message || '初始化失败'
    ElMessage.error(sdkError.value)
  }
}

/** 去除 Markdown 标记，用于语音朗读 */
function stripMarkdown(text: string): string {
  if (!text) return ''
  return text
    .replace(/```[\s\S]*?```/g, (m) => m.slice(3, -3).replace(/^[a-zA-Z0-9_+-]+\n/, '').trim())
    .replace(/`([^`]+)`/g, '$1')
    .replace(/!\[([^\]]*)\]\([^)]+\)/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/__([^_]+)__/g, '$1')
    .replace(/_([^_]+)_/g, '$1')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/^[-*+]\s+/gm, '')
    .replace(/^\d+\.\s+/gm, '')
    .replace(/^>\s+/gm, '')
    .replace(/^-{3,}$/gm, '')
    .replace(/^\*{3,}$/gm, '')
    .replace(/<[^>]+>/g, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

/** 转义 XML/SSML 特殊字符，避免被 SDK 解析为标签而截断 */
function escapeXml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

/** 驱动数字人朗读（单条完整文本，避免打断） */
function speakContent(text: string) {
  if (!avatar) return
  avatarState.value = 'speak'
  // 对 SSML 特殊字符做实体转义，防止内容被截断
  const safe = escapeXml(text)
  avatar.speak(safe, true, true)
}

/** 调用大模型 + 驱动数字人说话 */
async function speakText() {
  const text = inputText.value.trim()
  if ((!text && !pendingImages.value.length) || !avatar || aiLoading.value) return

  messages.value.push({
    role: 'user',
    content: text,
    attachmentUrls: pendingImages.value.map(item => item.url).filter(Boolean),
    attachmentBase64List: pendingImages.value.map(item => item.base64).filter(Boolean),
    attachmentNames: pendingImages.value.map(item => item.name),
  })
  const sentImages = pendingImages.value.map(item => item.file)
  const sentImageUrls = pendingImages.value.map(item => item.url)
  inputText.value = ''
  pendingImages.value = []

  avatarState.value = 'think'
  avatar?.think()
  aiLoading.value = true

  try {
    const safeMessages = messages.value
      .filter(m => m.role === 'user' || m.role === 'assistant')
      .map(m => ({ role: m.role, content: m.content || '' }))

    const res = await agentApi.chat(safeMessages, sentImages)

    messages.value.push({ role: 'assistant', content: res.message || '', toolCalls: res.tool_calls })

    const speakTextRaw = stripMarkdown(res.message || '抱歉，我没听明白。')
    speakContent(speakTextRaw)
  } catch (e: any) {
    const detail = e?.response?.data?.detail || e?.message || ''
    const errMsg = detail ? `抱歉，出错了：${detail}` : '抱歉，刚刚出错了。'
    avatarState.value = 'idle'
    avatar?.idle()
    ElMessage.error(errMsg)
  } finally {
    aiLoading.value = false
    sentImageUrls.forEach(url => {
      const stillUsed = messages.value.some(m => (m.attachmentUrls || []).includes(url) || m.attachmentUrl === url)
      if (!stillUsed) URL.revokeObjectURL(url)
    })
  }
}

/** 语音输入（与聊天区域保持一致） */
function toggleRecording() {
  if (isRecording.value) {
    stopRecording()
  } else {
    startRecording()
  }
  if (!(window as any).SpeechRecognition && !(window as any).webkitSpeechRecognition) {
    ElMessage.warning('当前浏览器不支持语音输入')
    return
  }
  startListening()
}

function startListening() {
  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
}

function startRecording() {
  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  if (!SpeechRecognition) {
    ElMessage.error('当前浏览器不支持语音识别，请使用 Chrome / Edge / Safari')
    return
  }
  recognition = new SpeechRecognition()
  recognition.lang = 'zh-CN'
  recognition.continuous = true
  recognition.interimResults = true
  finalTranscript = inputText.value

  recognition.onstart = () => {
    isRecording.value = true
    avatarState.value = 'listen'
    avatar?.listen()
  }

  recognition.onresult = (event: any) => {
    let interim = ''
    let final = ''
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript
      if (event.results[i].isFinal) {
        final += transcript
      } else {
        interim += transcript
      }
    }
    if (final) {
      finalTranscript += final
    }
    inputText.value = finalTranscript + interim
  }

  recognition.onerror = (event: any) => {
    if (event.error === 'no-speech') return
    ElMessage.error('语音识别错误: ' + event.error)
    stopRecording()
  }

  recognition.onend = () => {
    isRecording.value = false
  }

  recognition.start()
  recordingDuration.value = 0
  recordingTimer = window.setInterval(() => {
    recordingDuration.value++
  }, 1000)
}

function stopRecording() {
  if (recognition) {
    try { recognition.stop() } catch {}
  }
  isRecording.value = false
  recognition = null
  avatarState.value = 'idle'
  avatar?.idle()
  if (recordingTimer) {
    clearInterval(recordingTimer)
    recordingTimer = null
  }
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
    e.preventDefault()
    if (canSpeak.value) speakText()
  }
}

/** 页面隐藏时自动暂停，可见时恢复 */
function onVisibilityChange() {
  if (document.hidden) {
    stopRecording()
    avatar?.idle?.()
  }
}

onMounted(() => {
  document.body.style.overflow = 'hidden'
  initAvatar()
  document.addEventListener('visibilitychange', onVisibilityChange)
})
onUnmounted(() => {
  document.body.style.overflow = ''
  document.removeEventListener('visibilitychange', onVisibilityChange)
  stopListening()
  clearImage()
  stopRecording()
  avatar?.idle?.()
  setTimeout(() => avatar?.destroy?.(), 200)
})
</script>

<style scoped>
.avatar-page {
  height: calc(100vh - 60px);
  display: flex;
  flex-direction: column;
  background:
    radial-gradient(ellipse 80% 60% at 50% 120%, rgba(255,122,26,.12) 0%, transparent 60%),
    radial-gradient(ellipse 60% 50% at 20% 10%, rgba(59,130,246,.08) 0%, transparent 50%),
    radial-gradient(ellipse 60% 50% at 80% 10%, rgba(139,92,246,.08) 0%, transparent 50%),
    linear-gradient(135deg, #1a1f36 0%, #2c1a2e 50%, #1f2c4d 100%);
}
.avatar-page.fullscreen {
  height: 100vh;
}

.avatar-header {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 22px;
  color: #fff;
  border-bottom: 1px solid rgba(255,255,255,.06);
  flex-shrink: 0;
  background: rgba(15,23,42,.25);
  backdrop-filter: blur(6px);
}
.header-center {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  letter-spacing: .5px;
  padding: 6px 16px;
  border-radius: 20px;
  background: rgba(255,255,255,.06);
  border: 1px solid rgba(255,255,255,.08);
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #94a3b8;
  transition: background .3s ease;
}
.status-dot.listen { background: #3b82f6; animation: pulse 1.5s infinite; box-shadow: 0 0 8px rgba(59,130,246,.5); }
.status-dot.think { background: #f59e0b; box-shadow: 0 0 8px rgba(245,158,11,.4); }
.status-dot.speak { background: #10b981; box-shadow: 0 0 8px rgba(16,185,129,.4); }
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: .35; }
}
.status-text { color: rgba(255,255,255,.65); font-weight: 500; }

.avatar-stage {
  position: absolute;
  inset: 56px 0 0 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  padding-top: 0;
}
.avatar-container {
  width: 100%;
  max-width: 520px;
  height: 62vh;
  max-height: 680px;
  aspect-ratio: 540 / 960;
}
.avatar-placeholder {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: rgba(255,255,255,.5);
}
.error-text {
  color: #f87171;
  font-size: 13px;
  max-width: 400px;
  text-align: center;
}

.avatar-controls {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 0 22px 24px;
  display: flex;
  justify-content: center;
  z-index: 10;
}
.composer-glass {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  max-width: 760px;
  background: rgba(15, 23, 42, .55);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,.1);
  border-radius: 20px;
  padding: 14px 18px;
  box-shadow: 0 8px 32px rgba(0,0,0,.2), inset 0 1px 0 rgba(255,255,255,.06);
}
.composer-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.attach-preview-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  max-height: 92px;
  overflow-y: auto;
  padding-top: 2px;
}
.attach-preview {
  position: relative;
  display: inline-block;
}
.attach-preview img {
  width: 96px;
  height: 72px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,.1);
}
.attach-video {
  width: 96px;
  height: 72px;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,.1);
  background: rgba(255,255,255,.08);
  color: rgba(255,255,255,.72);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
  text-align: center;
  word-break: break-all;
  font-size: 11px;
}
.attach-remove {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 22px !important;
  height: 22px !important;
  background: rgba(255,255,255,.15) !important;
  border: 1px solid rgba(255,255,255,.2) !important;
  color: #fff !important;
  padding: 0 !important;
}
.attach-remove:hover {
  background: rgba(255,100,100,.3) !important;
}
.composer-tools {
  display: flex;
  align-items: center;
}
.attach-btn {
  color: rgba(255,255,255,.4) !important;
  padding: 4px !important;
}
.attach-btn:hover {
  color: rgba(255,255,255,.8) !important;
  background: rgba(255,255,255,.08) !important;
}
.text-input {
  flex: 1;
}
.text-input :deep(.el-textarea__inner) {
  background: transparent;
  border: none;
  color: #fff;
  border-radius: 0;
  padding: 4px 6px;
  font-size: 15px;
  line-height: 1.6;
  min-height: 44px !important;
  transition: all .2s ease;
  box-shadow: none !important;
}
.text-input :deep(.el-textarea__inner:focus) {
  background: transparent;
}
.text-input :deep(.el-textarea__inner::placeholder) {
  color: rgba(255,255,255,.3);
}
.control-btns {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
  align-items: center;
}
.control-btns :deep(.el-button) {
  transition: all .2s ease;
  border: none;
}
.control-btns :deep(.el-button:hover) {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 6px 20px rgba(0,0,0,.3);
}
.control-btns :deep(.el-button.is-disabled) {
  opacity: .3;
}
.send-btn {
  background: linear-gradient(135deg, #ff7a1a 0%, #d62828 100%) !important;
}
.send-btn:hover {
  background: linear-gradient(135deg, #ff8f3a 0%, #e04040 100%) !important;
}
.recording-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 10px;
  margin-bottom: 8px;
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.25);
  border-radius: 10px;
  animation: fade-in 0.2s ease;
}
@keyframes fade-in {
  from { opacity: 0; transform: translateY(-4px); }
  to   { opacity: 1; transform: translateY(0); }
}
.recording-wave {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 18px;
}
.recording-wave span {
  display: inline-block;
  width: 3px;
  height: 6px;
  background: #ef4444;
  border-radius: 2px;
  animation: wave-jump 0.6s infinite ease-in-out alternate;
}
@keyframes wave-jump {
  from { height: 4px; }
  to   { height: 16px; }
}
.recording-text {
  font-size: 13px;
  color: #fca5a5;
  font-weight: 500;
  flex: 1;
}
.recording-timer {
  font-size: 12px;
  color: #ef4444;
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}

.mic-wrap {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.mic-ripple {
  position: absolute;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(239, 68, 68, 0.15);
  animation: ripple-scale 1.5s infinite ease-out;
  pointer-events: none;
}
@keyframes ripple-scale {
  0%   { transform: scale(1); opacity: 0.6; }
  100% { transform: scale(2.2); opacity: 0; }
}

.mic-btn {
  background: rgba(255,255,255,.12) !important;
}
.mic-btn:hover {
  background: rgba(255,255,255,.2) !important;
}
.mic-btn.recording {
  color: #fff !important;
  background: #ef4444 !important;
  border-radius: 50% !important;
  animation: mic-pulse 1.2s infinite;
}
@keyframes mic-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
}

/* 思考气泡 */
.thinking-bubble {
  position: absolute;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(0,0,0,.45);
  backdrop-filter: blur(8px);
  padding: 10px 18px;
  border-radius: 24px;
  color: #fff;
  font-size: 13px;
}
.thinking-text { color: rgba(255,255,255,.85); }
.typing {
  display: flex;
  align-items: center;
  gap: 4px;
}
.typing span {
  width: 6px;
  height: 6px;
  background: #fff;
  border-radius: 50%;
  animation: typing 1.4s infinite both;
}
.typing span:nth-child(1) { animation-delay: 0s; }
.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing {
  0%, 80%, 100% { transform: scale(0.4); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* AI 回复气泡 */
.ai-msg-bubble {
  position: absolute;
  top: 68%;
  left: 50%;
  transform: translateX(-50%);
  max-width: 600px;
  z-index: 5;
  background: rgba(15, 23, 42, .72);
  backdrop-filter: blur(12px);
  padding: 14px 22px;
  border-radius: 16px;
  color: #fff;
  font-size: 14px;
  line-height: 1.7;
  text-align: center;
  border: 1px solid rgba(255,255,255,.08);
  box-shadow: 0 8px 32px rgba(0,0,0,.25);
  animation: bubbleIn .35s cubic-bezier(.4,0,.2,1);
}
.ai-msg-bubble::before {
  content: '';
  position: absolute;
  top: -6px;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 0;
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-bottom: 6px solid rgba(15, 23, 42, .72);
}
.ai-msg-md {
  margin: 0;
  max-height: 200px;
  overflow-y: auto;
  font-size: 14px;
  line-height: 1.7;
  color: #fff;
  padding-right: 4px;
  text-align: left;
}
.ai-msg-md::-webkit-scrollbar { width: 3px; }
.ai-msg-md::-webkit-scrollbar-thumb { background: rgba(255,255,255,.15); border-radius: 3px; }
.ai-msg-md :deep(p) { margin: 0 0 8px; color: #fff; }
.ai-msg-md :deep(p:last-child) { margin-bottom: 0; }
.ai-msg-md :deep(strong) { font-weight: 700; color: #fff; }
.ai-msg-md :deep(em) { font-style: italic; color: rgba(255,255,255,.9); }
.ai-msg-md :deep(a) { color: #ff7a1a; border-bottom: 1px solid rgba(255,122,26,.4); }
.ai-msg-md :deep(code) { background: rgba(255,255,255,.1); color: #fca5a5; padding: 1px 4px; border-radius: 3px; font-size: .9em; }
.ai-msg-md :deep(h1), .ai-msg-md :deep(h2), .ai-msg-md :deep(h3), .ai-msg-md :deep(h4), .ai-msg-md :deep(h5), .ai-msg-md :deep(h6) { font-size: 14px; font-weight: 700; margin: 0 0 6px; color: #fff; border: none; padding: 0; }
.ai-msg-md :deep(ul), .ai-msg-md :deep(ol) { padding-left: 18px; margin: 4px 0; }
.ai-msg-md :deep(li) { margin: 2px 0; }
.ai-msg-md :deep(blockquote) { border-left: 3px solid #ff7a1a; background: rgba(255,122,26,.08); padding: 4px 10px; margin: 6px 0; border-radius: 0 6px 6px 0; color: rgba(255,255,255,.85); }
.ai-msg-md :deep(hr) { border: none; border-top: 1px solid rgba(255,255,255,.15); margin: 8px 0; }
@keyframes bubbleIn {
  from { opacity: 0; transform: translateX(-50%) translateY(10px); }
  to   { opacity: 1; transform: translateX(-50%) translateY(0); }
}

/* 场景演练内容面板 */
.scenario-panel {
  position: absolute;
  top: 58%;
  left: 50%;
  transform: translateX(-50%);
  width: 90%;
  max-width: 560px;
  max-height: 30vh;
  z-index: 5;
  background: rgba(15, 23, 42, .78);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,.1);
  border-radius: 16px;
  padding: 16px 20px;
  color: #fff;
  font-size: 13px;
  line-height: 1.65;
  box-shadow: 0 8px 32px rgba(0,0,0,.3);
  animation: bubbleIn .35s cubic-bezier(.4,0,.2,1);
  overflow-y: auto;
}
.scenario-panel::-webkit-scrollbar { width: 4px; }
.scenario-panel::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,.15);
  border-radius: 4px;
}

.sp-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.sp-icon { font-size: 16px; }
.sp-title { font-weight: 700; font-size: 14px; flex: 1; }
.sp-count { font-size: 11px; color: rgba(255,255,255,.4); }

.sp-list-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.sp-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: rgba(255,255,255,.06);
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 10px;
  cursor: pointer;
  transition: all .2s ease;
}
.sp-item:hover {
  background: rgba(255,255,255,.1);
  border-color: rgba(255,255,255,.18);
  transform: translateY(-1px);
}
.sp-item-main { flex: 1; min-width: 0; }
.sp-item-title { font-weight: 600; font-size: 13px; margin-bottom: 4px; }
.sp-item-meta { display: flex; gap: 6px; margin-bottom: 4px; }
.sp-item-desc {
  font-size: 11px;
  color: rgba(255,255,255,.5);
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.sp-tag {
  display: inline-block;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(255,255,255,.1);
  color: rgba(255,255,255,.7);
}
.sp-tag.diff-低难度, .sp-tag.diff-low { background: rgba(16,185,129,.2); color: #6ee7b7; }
.sp-tag.diff-中难度, .sp-tag.diff-medium { background: rgba(245,158,11,.2); color: #fcd34d; }
.sp-tag.diff-高难度, .sp-tag.diff-high { background: rgba(239,68,68,.2); color: #fca5a5; }

.sp-tip {
  margin-top: 10px;
  font-size: 11px;
  color: rgba(255,255,255,.4);
  text-align: center;
}

.sp-content {
  max-height: 120px;
  overflow-y: auto;
  font-size: 12px;
  line-height: 1.7;
  color: rgba(255,255,255,.8);
  padding-right: 4px;
}
.sp-content::-webkit-scrollbar { width: 3px; }
.sp-content::-webkit-scrollbar-thumb { background: rgba(255,255,255,.15); border-radius: 3px; }

.sp-image {
  margin-bottom: 8px;
  border-radius: 8px;
  overflow: hidden;
  background: #000;
  display: flex;
  justify-content: center;
  max-height: 140px;
}
.sp-image img { max-width: 100%; object-fit: contain; }

.sp-desc {
  font-size: 12px;
  color: rgba(255,255,255,.7);
  line-height: 1.7;
  max-height: 80px;
  overflow-y: auto;
}

.sp-result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.sp-result-label { font-weight: 600; font-size: 13px; }
.sp-score {
  font-size: 28px;
  font-weight: 800;
  color: #f59e0b;
}
.sp-score span { font-size: 13px; font-weight: 500; margin-left: 2px; }
.sp-score.good { color: #10b981; }
.sp-score.pass { color: #f59e0b; }
.sp-score.fail { color: #ef4444; }

.sp-analysis { background: rgba(255,255,255,.06); border-radius: 10px; padding: 10px 12px; }
.sp-analysis-title { font-weight: 600; font-size: 12px; margin-bottom: 6px; color: rgba(255,255,255,.85); }
.sp-analysis-body { font-size: 12px; color: rgba(255,255,255,.7); line-height: 1.7; max-height: 120px; overflow-y: auto; }
.sp-analysis-body::-webkit-scrollbar { width: 3px; }
.sp-analysis-body::-webkit-scrollbar-thumb { background: rgba(255,255,255,.15); border-radius: 3px; }

/* 场景面板中 MarkdownText 深色适配 —— 强制白底白字，覆盖组件默认 var(--txt-primary) */
.sp-content :deep(.md),
.sp-desc :deep(.md),
.sp-analysis-body :deep(.md) { color: #fff !important; }

.sp-content :deep(p),
.sp-desc :deep(p),
.sp-analysis-body :deep(p) { color: rgba(255,255,255,.85); margin: 0 0 6px; }
.sp-content :deep(p:last-child),
.sp-desc :deep(p:last-child),
.sp-analysis-body :deep(p:last-child) { margin-bottom: 0; }
.sp-content :deep(strong),
.sp-desc :deep(strong),
.sp-analysis-body :deep(strong) { font-weight: 700; color: #fff; }
.sp-content :deep(a),
.sp-desc :deep(a),
.sp-analysis-body :deep(a) { color: #ff7a1a; border-bottom: 1px solid rgba(255,122,26,.4); }
.sp-content :deep(code),
.sp-desc :deep(code),
.sp-analysis-body :deep(code) { background: rgba(255,255,255,.1); color: #fca5a5; padding: 1px 4px; border-radius: 3px; font-size: .9em; }
.sp-content :deep(h1), .sp-content :deep(h2), .sp-content :deep(h3), .sp-content :deep(h4), .sp-content :deep(h5), .sp-content :deep(h6),
.sp-desc :deep(h1), .sp-desc :deep(h2), .sp-desc :deep(h3), .sp-desc :deep(h4), .sp-desc :deep(h5), .sp-desc :deep(h6),
.sp-analysis-body :deep(h1), .sp-analysis-body :deep(h2), .sp-analysis-body :deep(h3), .sp-analysis-body :deep(h4), .sp-analysis-body :deep(h5), .sp-analysis-body :deep(h6) { color: #fff; border: none; padding: 0; margin: 0 0 6px; font-size: 13px; }
.sp-content :deep(blockquote),
.sp-desc :deep(blockquote),
.sp-analysis-body :deep(blockquote) { border-left: 3px solid #ff7a1a; background: rgba(255,122,26,.1); padding: 4px 10px; margin: 6px 0; border-radius: 0 6px 6px 0; }
.sp-content :deep(ul), .sp-content :deep(ol),
.sp-desc :deep(ul), .sp-desc :deep(ol),
.sp-analysis-body :deep(ul), .sp-analysis-body :deep(ol) { padding-left: 18px; margin: 4px 0; }
.sp-content :deep(li),
.sp-desc :deep(li),
.sp-analysis-body :deep(li) { margin: 2px 0; }
</style>
