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
      <!-- 最近一条 AI 回复 -->
      <div v-if="lastAiMsg" class="ai-msg-bubble">
        <p class="ai-msg-text">{{ lastAiMsg }}</p>
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
          </div>
        </div>
        <div class="control-btns">
          <el-button
            :class="['mic-btn', { listening: isListening }]"
            :type="isListening ? 'danger' : 'primary'"
            :disabled="!sdkReady"
            circle
            size="large"
            @click="toggleListen"
          >
            <el-icon :size="20"><Microphone /></el-icon>
          </el-button>
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { agentApi } from '@/api/agent'
import type { AgentMessage } from '@/types'
import CameraCapture from '@/components/CameraCapture.vue'
import { extractVideoCover } from '@/utils/videoCover'

const route = useRoute()
const auth = useAuthStore()
const isFullscreen = computed(() => route.path === '/avatar-live')

const avatarState = ref<'idle' | 'listen' | 'think' | 'speak'>('idle')
const sdkReady = ref(false)
const sdkError = ref('')
const inputText = ref('')
const isListening = ref(false)
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

    messages.value.push({ role: 'assistant', content: res.message || '' })

    const speakContent = res.message || '抱歉，我没听明白。'
    avatarState.value = 'speak'
    avatar.speak(speakContent, true, true)
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

/** 语音输入 */
function toggleListen() {
  if (isListening.value) {
    stopListening()
    return
  }
  if (!(window as any).SpeechRecognition && !(window as any).webkitSpeechRecognition) {
    ElMessage.warning('当前浏览器不支持语音输入')
    return
  }
  startListening()
}

function startListening() {
  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  recognition = new SpeechRecognition()
  recognition.lang = 'zh-CN'
  recognition.continuous = false
  recognition.interimResults = false

  recognition.onstart = () => {
    isListening.value = true
    avatarState.value = 'listen'
    avatar?.listen()
  }

  recognition.onresult = (event: any) => {
    const transcript = event.results[0][0].transcript
    inputText.value = transcript
    setTimeout(() => speakText(), 300)
  }

  recognition.onerror = () => {
    isListening.value = false
    avatarState.value = 'idle'
    avatar?.idle()
    ElMessage.error('语音识别失败')
  }

  recognition.onend = () => {
    isListening.value = false
  }

  recognition.start()
}

function stopListening() {
  recognition?.stop()
  isListening.value = false
  avatarState.value = 'idle'
  avatar?.idle()
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
    stopListening()
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
.mic-btn {
  background: rgba(255,255,255,.12) !important;
}
.mic-btn:hover {
  background: rgba(255,255,255,.2) !important;
}
.mic-btn.listening {
  animation: micPulse 1.5s infinite;
}
@keyframes micPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(239,68,68,.4); }
  50% { box-shadow: 0 0 0 10px rgba(239,68,68,0); }
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
.ai-msg-text {
  margin: 0;
  max-height: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
}
@keyframes bubbleIn {
  from { opacity: 0; transform: translateX(-50%) translateY(10px); }
  to   { opacity: 1; transform: translateX(-50%) translateY(0); }
}
</style>
