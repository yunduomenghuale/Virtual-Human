<template>
  <div class="avatar-showcase" :class="{ fullscreen: isFullscreen }">
    <!-- 扫描线纹理层 -->
    <div class="scanlines" />
    <!-- 动态径向光 -->
    <div class="ambient-glow tl" />
    <div class="ambient-glow br" />

    <!-- 顶部状态栏 -->
    <header class="showcase-header">
      <div class="header-left">
        <div class="logo-mark">
          <span class="logo-icon">
            <el-icon :size="16" color="#fff"><AlarmClock /></el-icon>
          </span>
          <span class="logo-text">智安 ZHIAN</span>
        </div>
        <div class="header-sep" />
        <span class="header-sub">实验室消防安全 AI 指挥系统</span>
      </div>
      <div class="header-center">
        <span class="status-light" :class="avatarState" />
        <span class="status-code">{{ stateCode }}</span>
      </div>
      <div class="header-right">
        <el-button v-if="!isFullscreen" text class="back-btn" @click="$router.push('/agent')">
          <el-icon><ArrowLeft /></el-icon>
          <span>返回</span>
        </el-button>
        <div v-else class="time-display">{{ currentTime }}</div>
      </div>
    </header>

    <!-- 主体三栏 -->
    <main class="showcase-body">
      <!-- 左侧：全功能展示 -->
      <aside class="panel-left">
        <div class="left-inner">
          <!-- 品牌头 -->
          <div class="brand-block">
            <div class="brand-tag">AI SAFETY PLATFORM</div>
            <h1 class="brand-title">智安平台</h1>
            <p class="brand-desc">以 3D 数字人为交互入口、以大模型为智能引擎的实验室消防安全 AI 助手系统</p>
          </div>

          <!-- 三核心价值 -->
          <div class="prop-row">
            <div class="prop-card">
              <div class="prop-ico">
                <el-icon :size="22"><View /></el-icon>
              </div>
              <div class="prop-name">看得见</div>
              <div class="prop-detail">3D 数字人实时驱动</div>
            </div>
            <div class="prop-card">
              <div class="prop-ico">
                <el-icon :size="22"><Cpu /></el-icon>
              </div>
              <div class="prop-name">懂得多</div>
              <div class="prop-detail">大模型全链路覆盖</div>
            </div>
            <div class="prop-card">
              <div class="prop-ico">
                <el-icon :size="22"><TrendCharts /></el-icon>
              </div>
              <div class="prop-name">防得住</div>
              <div class="prop-detail">事前预防智能预警</div>
            </div>
          </div>

          <!-- 功能矩阵 -->
          <div class="matrix-section">
            <div class="matrix-title">
              <span class="matrix-line" />
              <span>核心能力矩阵</span>
              <span class="matrix-line" />
            </div>
            <div class="matrix-grid">
              <div class="matrix-item">
                <div class="mx-icon"><el-icon :size="16"><ChatDotRound /></el-icon></div>
                <div class="mx-info">
                  <div class="mx-name">知识问答</div>
                  <div class="mx-desc">基于 RAG 的消防规范检索</div>
                </div>
                <div class="mx-dot active" />
              </div>
              <div class="matrix-item">
                <div class="mx-icon"><el-icon :size="16"><Camera /></el-icon></div>
                <div class="mx-info">
                  <div class="mx-name">隐患识别</div>
                  <div class="mx-desc">图片+视频多模态检测</div>
                </div>
                <div class="mx-dot active" />
              </div>
              <div class="matrix-item">
                <div class="mx-icon"><el-icon :size="16"><Document /></el-icon></div>
                <div class="mx-info">
                  <div class="mx-name">报告生成</div>
                  <div class="mx-desc">PDF / Word 一键输出</div>
                </div>
                <div class="mx-dot active" />
              </div>
              <div class="matrix-item">
                <div class="mx-icon"><el-icon :size="16"><Reading /></el-icon></div>
                <div class="mx-info">
                  <div class="mx-name">场景演练</div>
                  <div class="mx-desc">AI 教官教学+实战评分</div>
                </div>
                <div class="mx-dot active" />
              </div>
              <div class="matrix-item">
                <div class="mx-icon"><el-icon :size="16"><Search /></el-icon></div>
                <div class="mx-info">
                  <div class="mx-name">根因分析</div>
                  <div class="mx-desc">四维因果推理诊断</div>
                </div>
                <div class="mx-dot active" />
              </div>
              <div class="matrix-item">
                <div class="mx-icon"><el-icon :size="16"><DataLine /></el-icon></div>
                <div class="mx-info">
                  <div class="mx-name">风险预测</div>
                  <div class="mx-desc">时间序列+季节预测</div>
                </div>
                <div class="mx-dot active" />
              </div>
            </div>
          </div>

          <!-- 应用价值 -->
          <div class="value-section">
            <div class="value-title">应用价值</div>
            <div class="value-list">
              <div class="value-row">
                <div class="value-num">01</div>
                <div class="value-body">
                  <strong>交互革新</strong>
                  <span>从"纸质台账"走向"智能对话"</span>
                </div>
              </div>
              <div class="value-row">
                <div class="value-num">02</div>
                <div class="value-body">
                  <strong>能力闭环</strong>
                  <span>识别→分析→报告→培训→预测</span>
                </div>
              </div>
              <div class="value-row">
                <div class="value-num">03</div>
                <div class="value-body">
                  <strong>模式升级</strong>
                  <span>从"事后处置"走向"事前预防"</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 底部 -->
          <div class="left-footer">
            <div class="footer-bar" />
            <p>24 小时在线 · 永不疲倦 · 不断学习的 AI 安全专家</p>
          </div>
        </div>
      </aside>

      <!-- 中间：数字人 + 字幕 -->
      <section class="panel-center">
        <div class="avatar-stage">
          <div class="avatar-wrapper">
            <div id="avatar-container" class="avatar-container"></div>
          </div>
          <div v-if="!sdkReady" class="avatar-placeholder">
            <div class="loader-ring"><span /><span /><span /></div>
            <p class="placeholder-text">数字人初始化中...</p>
            <p v-if="sdkError" class="error-text">{{ sdkError }}</p>
          </div>

          <!-- 字幕 -->
          <div class="subtitle-wrapper">
            <transition name="subtitle-fade">
              <div v-if="currentSubtitle" class="subtitle-bar">
                <div class="subtitle-scan" />
                <p class="subtitle-text">{{ currentSubtitle }}</p>
              </div>
            </transition>
            <transition name="subtitle-fade">
              <div v-if="aiLoading" class="subtitle-bar thinking">
                <div class="subtitle-scan" />
                <div class="thinking-dots"><span /><span /><span /></div>
                <span class="thinking-label">小安正在思考</span>
              </div>
            </transition>
          </div>
        </div>

        <!-- 控制栏 -->
        <div class="control-dock">
          <div class="dock-inner">
            <div v-if="pendingImages.length" class="attach-strip">
              <div v-for="(item, idx) in pendingImages" :key="item.key" class="attach-thumb">
                <img v-if="item.url" :src="item.url" />
                <div v-else class="attach-video-label">{{ item.name }}</div>
                <button class="attach-close" @click="removeImage(idx)">
                  <el-icon><Close /></el-icon>
                </button>
              </div>
            </div>
            <div class="input-row">
              <el-input
                v-model="inputText"
                type="textarea"
                :rows="1"
                placeholder="输入文字与小安对话，或点击麦克风语音输入..."
                resize="none"
                class="dock-input"
                @keydown="onKeydown"
              />
              <div class="dock-actions">
                <el-upload multiple :auto-upload="false" :show-file-list="false" :on-change="onPick" accept="image/png,image/jpeg,video/mp4,video/webm,video/quicktime">
                  <el-button text circle class="dock-btn" :disabled="!canUseHazard"><el-icon :size="18"><Plus /></el-icon></el-button>
                </el-upload>
                <el-button text circle class="dock-btn" :disabled="!canUseHazard" @click="cameraVisible = true"><el-icon :size="18"><Camera /></el-icon></el-button>
                <el-button circle class="dock-btn mic" :class="{ recording: isRecording }" :title="isRecording ? '点击结束录音' : '语音输入'" @click="toggleRecording"><el-icon :size="18"><Microphone /></el-icon></el-button>
                <el-button type="primary" circle class="dock-btn send" :disabled="!canSpeak" @click="speakText"><el-icon :size="18"><Promotion /></el-icon></el-button>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 右侧：视频 + 轮播 -->
      <aside class="panel-right">
        <div class="right-inner">
          <!-- 视频区 -->
          <div class="media-block">
            <div class="media-header">
              <span class="media-dot blink" />
              <span class="media-label">系统演示</span>
              <span class="media-tag">LIVE</span>
            </div>
            <div class="media-frame">
              <video ref="videoRef" src="/showcase/video/视频展示.mp4" muted loop playsinline autoplay class="media-video" />
              <div class="media-corner tl" /><div class="media-corner tr" /><div class="media-corner bl" /><div class="media-corner br" />
            </div>
          </div>

          <!-- 轮播区 -->
          <div class="media-block">
            <div class="media-header">
              <span class="media-dot" />
              <span class="media-label">功能概览</span>
              <span class="media-counter">{{ currentSlide + 1 }} / {{ carouselImages.length }}</span>
            </div>
            <div class="media-frame carousel-frame">
              <img
                v-for="(src, i) in carouselImages"
                :key="src"
                :src="src"
                class="carousel-img"
                :class="{ active: currentSlide === i }"
                alt="功能截图"
              />
              <div class="media-corner tl" /><div class="media-corner tr" /><div class="media-corner bl" /><div class="media-corner br" />
              <div class="carousel-dots">
                <button v-for="(_, i) in carouselImages" :key="i" class="dot" :class="{ active: currentSlide === i }" @click="currentSlide = i" />
              </div>
              <button class="carousel-arrow prev" @click="prevSlide"><el-icon><ArrowLeft /></el-icon></button>
              <button class="carousel-arrow next" @click="nextSlide"><el-icon><ArrowRight /></el-icon></button>
            </div>
          </div>
        </div>
      </aside>
    </main>

    <CameraCapture v-model="cameraVisible" @capture="addPendingImage" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { agentApi } from '@/api/agent'
import CameraCapture from '@/components/CameraCapture.vue'
import { extractVideoCover } from '@/utils/videoCover'
import type { AgentMessage } from '@/types'

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
const currentSubtitle = ref('')
const currentTime = ref('')
const videoRef = ref<HTMLVideoElement | null>(null)

let avatar: any = null
let recognition: any = null
let subtitleTimer: number | null = null

const carouselImages = [
  '/showcase/images/1登录页.png',
  '/showcase/images/2首页.png',
  '/showcase/images/3小安聊天区域.png',
  '/showcase/images/5报告详情.png',
  '/showcase/images/6深度分析.png',
  '/showcase/images/7风险预测.png',
]
const currentSlide = ref(0)
let carouselInterval: number | null = null

function nextSlide() { currentSlide.value = (currentSlide.value + 1) % carouselImages.length }
function prevSlide() { currentSlide.value = (currentSlide.value - 1 + carouselImages.length) % carouselImages.length }
function startCarousel() { carouselInterval = window.setInterval(nextSlide, 4000) }
function stopCarousel() { if (carouselInterval) clearInterval(carouselInterval) }

/** 预加载轮播图片，避免切换时白屏/黑屏 */
function preloadCarouselImages() {
  carouselImages.forEach((src) => {
    const img = new Image()
    img.src = src
  })
}

function updateTime() {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}
let timeInterval: number | null = null

const stateLabel = computed(() => {
  const map: Record<string, string> = { idle: '待机中', listen: '倾听中', think: '思考中', speak: '播报中' }
  return map[avatarState.value] || '待机中'
})
const stateCode = computed(() => {
  const map: Record<string, string> = { idle: 'STANDBY', listen: 'RECV', think: 'PROC', speak: 'TX' }
  return map[avatarState.value] || 'STANDBY'
})

const canUseHazard = computed(() => auth.hasSkill('hazard_detect'))
const canSpeak = computed(() => sdkReady.value && !aiLoading.value && (inputText.value.trim().length > 0 || pendingImages.value.length > 0))

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
        if (blob) { resolve(new File([blob], file.name, { type: 'image/jpeg' })) }
        else { reject(new Error('压缩失败')) }
        URL.revokeObjectURL(img.src)
      }, 'image/jpeg', quality)
    }
    img.onerror = () => { URL.revokeObjectURL(img.src); reject(new Error('图片加载失败')) }
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
    img.onerror = () => { URL.revokeObjectURL(img.src); reject(new Error('图片加载失败')) }
    img.src = URL.createObjectURL(file)
  })
}

async function onPick(f: any) {
  const real = (f.raw || f) as File | undefined
  if (!real) return
  if (!canUseHazard.value) { ElMessage.warning('当前角色未启用「隐患识别」skill'); return }
  await addPendingImage(real)
}

async function addPendingImage(file: File) {
  if (file.type.startsWith('video/')) {
    let cover = ''
    try { cover = await extractVideoCover(file) } catch { cover = '' }
    pendingImages.value.push({ file, url: cover, base64: '', name: file.name, key: `${file.name}-${file.lastModified}-${Date.now()}` })
    ElMessage.success('视频已加入待识别列表')
    return
  }
  try { const compressed = await compressImageFile(file, 1200, 0.8); await pushPendingImage(compressed, file.name) }
  catch { await pushPendingImage(file, file.name) }
}

async function pushPendingImage(file: File, originalName: string) {
  const url = URL.createObjectURL(file)
  let base64 = ''
  try { base64 = await compressImageToBase64(file, 800, 0.7) } catch { base64 = '' }
  pendingImages.value.push({ file, url, base64, name: originalName, key: `${originalName}-${file.lastModified}-${Date.now()}` })
}

function removeImage(index: number) {
  const [removed] = pendingImages.value.splice(index, 1)
  if (removed) URL.revokeObjectURL(removed.url)
}
function clearImage() {
  pendingImages.value.forEach(item => URL.revokeObjectURL(item.url))
  pendingImages.value = []
}

function loadSdk(): Promise<void> {
  return new Promise((resolve, reject) => {
    if ((window as any).XmovAvatar) { resolve(); return }
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
    if (!XmovAvatar) throw new Error('SDK 未正确加载')
    const APP_ID = import.meta.env.VITE_XINGYUN_APP_ID || ''
    const APP_SECRET = import.meta.env.VITE_XINGYUN_APP_SECRET || ''
    if (!APP_ID || !APP_SECRET) { sdkError.value = '请在 .env 中配置 VITE_XINGYUN_APP_ID 和 VITE_XINGYUN_APP_SECRET'; return }
    avatar = new XmovAvatar({
      containerId: '#avatar-container', appId: APP_ID, appSecret: APP_SECRET,
      gatewayServer: 'https://nebula-agent.xingyun3d.com/user/v1/ttsa/session',
      onMessage(msg: any) { console.log('[Avatar SDK]', msg) },
      onStateChange(state: string) { console.log('[Avatar State]', state) },
      onVoiceStateChange(status: 'start' | 'end') {
        if (status === 'start') avatarState.value = 'speak'
        if (status === 'end') {
          avatarState.value = 'idle'
          if (subtitleTimer) clearTimeout(subtitleTimer)
          subtitleTimer = window.setTimeout(() => { currentSubtitle.value = '' }, 3000)
        }
      },
    })
    await avatar.init({
      onDownloadProgress: (p: number) => console.log(`加载进度: ${p}%`),
      onError: (err: any) => { sdkError.value = String(err); console.error('Avatar init error:', err) },
    })
    sdkReady.value = true
    avatar.idle()
    // SDK 初始化完成后，异步修正 canvas 居中偏移
    requestAnimationFrame(() => { requestAnimationFrame(fixAvatarCenter) })
  } catch (e: any) {
    sdkError.value = e?.message || '初始化失败'
    ElMessage.error(sdkError.value)
  }
}

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
    .replace(/^&gt;\s+/gm, '')
    .replace(/^-{3,}$/gm, '')
    .replace(/^\*{3,}$/gm, '')
    .replace(/<[^>]+>/g, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

function escapeXml(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function speakContent(text: string) {
  if (!avatar) return
  avatarState.value = 'speak'
  currentSubtitle.value = text
  const safe = escapeXml(text)
  avatar.speak(safe, true, true)
}

async function speakText() {
  const text = inputText.value.trim()
  if ((!text && !pendingImages.value.length) || !avatar || aiLoading.value) return
  messages.value.push({
    role: 'user', content: text,
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
  currentSubtitle.value = ''
  try {
    const safeMessages = messages.value.filter(m => m.role === 'user' || m.role === 'assistant').map(m => ({ role: m.role, content: m.content || '' }))
    const res = await agentApi.chat(safeMessages, sentImages)
    messages.value.push({ role: 'assistant', content: res.message || '', toolCalls: res.tool_calls })
    const speakTextRaw = stripMarkdown(res.message || '抱歉，我没听明白。')
    speakContent(speakTextRaw)
  } catch (e: any) {
    const detail = e?.response?.data?.detail || e?.message || ''
    const errMsg = detail ? `抱歉，出错了：${detail}` : '抱歉，刚刚出错了。'
    avatarState.value = 'idle'
    avatar?.idle()
    currentSubtitle.value = ''
    ElMessage.error(errMsg)
  } finally {
    aiLoading.value = false
    sentImageUrls.forEach(url => {
      const stillUsed = messages.value.some(m => (m.attachmentUrls || []).includes(url) || m.attachmentUrl === url)
      if (!stillUsed) URL.revokeObjectURL(url)
    })
  }
}

function toggleRecording() {
  if (isRecording.value) { stopRecording() }
  else {
    if (!(window as any).SpeechRecognition && !(window as any).webkitSpeechRecognition) { ElMessage.warning('当前浏览器不支持语音输入'); return }
    startRecording()
  }
}

function startRecording() {
  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  if (!SpeechRecognition) { ElMessage.error('当前浏览器不支持语音识别'); return }
  recognition = new SpeechRecognition()
  recognition.lang = 'zh-CN'
  recognition.continuous = true
  recognition.interimResults = true
  finalTranscript = inputText.value
  recognition.onstart = () => { isRecording.value = true; avatarState.value = 'listen'; avatar?.listen() }
  recognition.onresult = (event: any) => {
    let interim = ''; let final = ''
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript
      if (event.results[i].isFinal) final += transcript
      else interim += transcript
    }
    if (final) finalTranscript += final
    inputText.value = finalTranscript + interim
  }
  recognition.onerror = (event: any) => { if (event.error === 'no-speech') return; ElMessage.error('语音识别错误: ' + event.error); stopRecording() }
  recognition.onend = () => { isRecording.value = false }
  recognition.start()
  recordingDuration.value = 0
  recordingTimer = window.setInterval(() => recordingDuration.value++, 1000)
}

function stopRecording() {
  if (recognition) { try { recognition.stop() } catch {} }
  isRecording.value = false
  recognition = null
  avatarState.value = 'idle'
  avatar?.idle()
  if (recordingTimer) { clearInterval(recordingTimer); recordingTimer = null }
}

/** 动态修正 canvas 在容器内的居中偏移（SDK 内部渲染存在固有偏移，且随分辨率变化） */
function fixAvatarCenter() {
  const container = document.getElementById('avatar-container')
  const canvas = container?.querySelector('canvas')
  const wrapper = document.querySelector('.avatar-wrapper') as HTMLElement | null
  if (!container || !canvas || !wrapper) return

  const wrapRect = wrapper.getBoundingClientRect()
  const canvasRect = canvas.getBoundingClientRect()

  // 计算 canvas 当前在 wrapper 内的水平偏移
  const currentLeft = canvasRect.left - wrapRect.left
  const expectedLeft = (wrapRect.width - canvasRect.width) / 2
  const offset = expectedLeft - currentLeft

  // 应用到父容器（SDK 会覆盖 canvas 自身的 transform）
  container.style.transform = `translateX(${offset}px)`
}

let resizeFixTimer: number | null = null
function onResizeFix() {
  if (resizeFixTimer) clearTimeout(resizeFixTimer)
  resizeFixTimer = window.setTimeout(fixAvatarCenter, 100)
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); if (canSpeak.value) speakText() }
}

function onVisibilityChange() {
  if (document.hidden) {
    stopRecording()
    avatar?.idle?.()
    if (videoRef.value) videoRef.value.pause()
  } else {
    if (videoRef.value) videoRef.value.play().catch(() => {})
  }
}

onMounted(() => {
  document.body.style.overflow = 'hidden'
  initAvatar()
  preloadCarouselImages()
  startCarousel()
  updateTime()
  timeInterval = window.setInterval(updateTime, 1000)
  document.addEventListener('visibilitychange', onVisibilityChange)
  window.addEventListener('resize', onResizeFix)
})

onUnmounted(() => {
  document.body.style.overflow = ''
  stopCarousel()
  if (timeInterval) clearInterval(timeInterval)
  if (subtitleTimer) clearTimeout(subtitleTimer)
  if (resizeFixTimer) clearTimeout(resizeFixTimer)
  document.removeEventListener('visibilitychange', onVisibilityChange)
  window.removeEventListener('resize', onResizeFix)
  stopRecording()
  clearImage()
  avatar?.idle?.()
  setTimeout(() => avatar?.destroy?.(), 200)
})
</script>

<style scoped>
/* ================= 底层环境与扫描线 ================= */
.avatar-showcase {
  height: 100vh; width: 100vw; overflow: hidden;
  display: flex; flex-direction: column;
  background:
    radial-gradient(ellipse 60% 40% at 20% 10%, rgba(6,182,212,.06) 0%, transparent 50%),
    radial-gradient(ellipse 60% 40% at 80% 90%, rgba(255,122,26,.05) 0%, transparent 50%),
    linear-gradient(180deg, #070a12 0%, #0b101c 50%, #080b14 100%);
  position: relative;
  color: #cbd5e1;
}

.scanlines {
  position: absolute; inset: 0;
  background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,.08) 2px, rgba(0,0,0,.08) 4px);
  pointer-events: none; z-index: 0;
}

.ambient-glow {
  position: absolute; width: 400px; height: 400px; border-radius: 50%;
  filter: blur(120px); opacity: .18; pointer-events: none; z-index: 0;
}
.ambient-glow.tl { top: -150px; left: -150px; background: rgba(6,182,212,.6); }
.ambient-glow.br { bottom: -150px; right: -150px; background: rgba(255,122,26,.5); }

/* ================= 顶部栏 ================= */
.showcase-header {
  height: 48px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 20px;
  border-bottom: 1px solid rgba(255,255,255,.06);
  background: rgba(7,10,18,.7);
  backdrop-filter: blur(12px);
  position: relative; z-index: 10;
}
.header-left { display: flex; align-items: center; gap: 10px; }
.logo-mark {
  display: flex; align-items: center; gap: 6px;
}
.logo-icon {
  width: 26px; height: 26px; border-radius: 6px;
  background: linear-gradient(135deg, #ff7a1a, #d62828);
  display: flex; align-items: center; justify-content: center;
}
.logo-text {
  font-size: 14px; font-weight: 800; color: #fff;
  letter-spacing: 1.5px;
}
.header-sep { width: 1px; height: 16px; background: rgba(255,255,255,.12); }
.header-sub { font-size: 11px; color: rgba(255,255,255,.35); letter-spacing: .5px; }

.header-center {
  display: flex; align-items: center; gap: 8px;
  padding: 4px 12px; border-radius: 4px;
  background: rgba(255,255,255,.03);
  border: 1px solid rgba(255,255,255,.06);
}
.status-light {
  width: 7px; height: 7px; border-radius: 50%;
  background: #475569; transition: all .3s ease;
}
.status-light.listen { background: #0ea5e9; box-shadow: 0 0 8px rgba(14,165,233,.5); animation: blink 1.2s infinite; }
.status-light.think { background: #f59e0b; box-shadow: 0 0 8px rgba(245,158,11,.4); }
.status-light.speak { background: #22c55e; box-shadow: 0 0 8px rgba(34,197,94,.4); }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }
.status-code { font-size: 11px; color: rgba(255,255,255,.45); font-family: 'SF Mono', 'Consolas', monospace; letter-spacing: .5px; }

.header-right { display: flex; align-items: center; }
.back-btn { color: rgba(255,255,255,.4) !important; font-size: 12px !important; }
.back-btn:hover { color: rgba(255,255,255,.85) !important; background: rgba(255,255,255,.05) !important; }
.time-display { font-size: 12px; color: rgba(255,255,255,.3); font-family: 'SF Mono', 'Consolas', monospace; }

/* ================= 主体三栏 ================= */
.showcase-body {
  flex: 1; display: grid;
  grid-template-columns: 400px 1fr 420px;
  gap: 14px;
  padding: 12px 16px 14px;
  min-height: 0;
}

/* ================= 左侧 ================= */
.panel-left { min-width: 0; overflow: hidden; }
.left-inner {
  height: 100%; background: rgba(255,255,255,.02);
  border: 1px solid rgba(255,255,255,.06);
  border-radius: 10px;
  padding: 18px 16px;
  display: flex; flex-direction: column; gap: 16px;
  overflow-y: auto;
}
.left-inner::-webkit-scrollbar { width: 3px; }
.left-inner::-webkit-scrollbar-thumb { background: rgba(255,255,255,.08); border-radius: 3px; }

.brand-block { text-align: left; }
.brand-tag {
  font-size: 10px; color: rgba(255,122,26,.7); letter-spacing: 2px;
  font-weight: 600; margin-bottom: 4px;
}
.brand-title {
  font-size: 26px; font-weight: 900; color: #fff;
  margin: 0 0 6px; letter-spacing: 2px;
}
.brand-desc {
  font-size: 12px; color: rgba(255,255,255,.4);
  line-height: 1.6; margin: 0;
}

/* 三核心价值横排 */
.prop-row { display: flex; gap: 8px; }
.prop-card {
  flex: 1; text-align: center;
  padding: 12px 6px;
  border-radius: 8px;
  background: rgba(255,255,255,.025);
  border: 1px solid rgba(255,255,255,.05);
  transition: all .2s ease;
}
.prop-card:hover { background: rgba(255,255,255,.05); border-color: rgba(255,255,255,.1); }
.prop-ico {
  width: 34px; height: 34px; margin: 0 auto 6px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(6,182,212,.15), rgba(59,130,246,.15));
  color: #7dd3fc;
}
.prop-name { font-size: 12px; font-weight: 700; color: rgba(255,255,255,.85); margin-bottom: 2px; }
.prop-detail { font-size: 10px; color: rgba(255,255,255,.35); line-height: 1.4; }

/* 功能矩阵 */
.matrix-section { flex-shrink: 0; }
.matrix-title {
  display: flex; align-items: center; gap: 8px;
  font-size: 11px; color: rgba(255,255,255,.45);
  letter-spacing: 1px; margin-bottom: 10px;
}
.matrix-line { flex: 1; height: 1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,.1), transparent); }
.matrix-grid { display: flex; flex-direction: column; gap: 6px; }
.matrix-item {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 10px;
  border-radius: 6px;
  background: rgba(255,255,255,.02);
  border: 1px solid rgba(255,255,255,.04);
  transition: all .15s ease;
}
.matrix-item:hover { background: rgba(6,182,212,.06); border-color: rgba(6,182,212,.15); }
.mx-icon {
  width: 28px; height: 28px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  border-radius: 6px;
  background: rgba(255,255,255,.05);
  color: rgba(255,255,255,.4);
}
.matrix-item:hover .mx-icon { color: #38bdf8; }
.mx-info { flex: 1; min-width: 0; }
.mx-name { font-size: 12px; font-weight: 600; color: rgba(255,255,255,.8); }
.mx-desc { font-size: 10px; color: rgba(255,255,255,.35); margin-top: 1px; }
.mx-dot {
  width: 5px; height: 5px; border-radius: 50%;
  background: #334155; flex-shrink: 0;
}
.mx-dot.active { background: #22c55e; box-shadow: 0 0 4px rgba(34,197,94,.4); }

/* 应用价值 */
.value-section { flex-shrink: 0; }
.value-title {
  font-size: 11px; color: rgba(255,255,255,.45);
  letter-spacing: 1px; margin-bottom: 8px;
}
.value-list { display: flex; flex-direction: column; gap: 6px; }
.value-row {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 8px 10px;
  border-radius: 6px;
  background: rgba(255,255,255,.02);
  border-left: 2px solid rgba(255,122,26,.4);
}
.value-num {
  font-size: 10px; font-weight: 700; color: rgba(255,122,26,.6);
  font-family: 'SF Mono', 'Consolas', monospace;
  line-height: 1.4;
}
.value-body { display: flex; flex-direction: column; gap: 1px; }
.value-body strong { font-size: 12px; color: rgba(255,255,255,.75); }
.value-body span { font-size: 11px; color: rgba(255,255,255,.35); }

/* 底部 */
.left-footer { margin-top: auto; padding-top: 6px; }
.footer-bar { height: 1px; background: linear-gradient(90deg, transparent, rgba(255,122,26,.3), transparent); margin-bottom: 8px; }
.left-footer p { font-size: 10px; color: rgba(255,255,255,.25); text-align: center; margin: 0; font-style: italic; }

/* ================= 中间：数字人 ================= */
.panel-center { display: flex; flex-direction: column; min-width: 0; position: relative; }
.avatar-stage {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  position: relative; min-height: 0;
  background:
    url('/avatar-bg.jpg') center/cover no-repeat,
    linear-gradient(180deg, #070a12 0%, #0b101c 50%, #080b14 100%);
}
.avatar-wrapper {
  width: 460px;
  max-width: 100%;
  height: 62vh;
  max-height: 600px;
  position: relative;
  margin: 0 auto;
  overflow: hidden;
}
/* SDK 挂载点：占满 wrapper，用 flex 强制 canvas 居中 */
.avatar-container {
  width: 100%;
  height: 100%;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}
/* 阻止 SDK 错误的 absolute 定位 */
.avatar-container canvas {
  position: static !important;
  inset: auto !important;
  left: auto !important;
  transform: none !important;
  margin: 0 !important;
}
.avatar-placeholder {
  position: absolute; inset: 0;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 14px;
  color: rgba(255,255,255,.35);
}
.loader-ring { position: relative; width: 44px; height: 44px; }
.loader-ring span { position: absolute; inset: 0; border-radius: 50%; border: 2px solid transparent; border-top-color: #ff7a1a; animation: spin 1.2s linear infinite; }
.loader-ring span:nth-child(2) { inset: 5px; border-top-color: #0ea5e9; animation-duration: .9s; animation-direction: reverse; }
.loader-ring span:nth-child(3) { inset: 10px; border-top-color: #22c55e; animation-duration: .6s; }
@keyframes spin { to { transform: rotate(360deg); } }
.placeholder-text { font-size: 13px; color: rgba(255,255,255,.35); margin: 0; }
.error-text { font-size: 11px; color: #f87171; max-width: 300px; text-align: center; margin: 0; }

/* 字幕 */
.subtitle-wrapper {
  position: absolute; bottom: 14px; left: 50%;
  transform: translateX(-50%);
  width: 92%; max-width: 560px; z-index: 5; pointer-events: none;
}
.subtitle-bar {
  position: relative; padding: 12px 20px;
  border-radius: 10px;
  background: rgba(7,10,18,.82);
  backdrop-filter: blur(14px);
  border: 1px solid rgba(255,255,255,.08);
  text-align: center; overflow: hidden;
}
.subtitle-scan {
  position: absolute; top: 0; left: -100%; width: 60%; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,122,26,.7), transparent);
  animation: scan-glide 3s linear infinite;
}
@keyframes scan-glide { 0%{left:-60%} 100%{left:160%} }
.subtitle-text { margin: 0; font-size: 14px; line-height: 1.6; color: rgba(255,255,255,.9); }
.subtitle-bar.thinking { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 10px 20px; }
.thinking-dots { display: flex; align-items: center; gap: 3px; }
.thinking-dots span { width: 5px; height: 5px; border-radius: 50%; background: #f59e0b; animation: dot-bounce 1.4s infinite ease-in-out both; }
.thinking-dots span:nth-child(1) { animation-delay: -.32s; }
.thinking-dots span:nth-child(2) { animation-delay: -.16s; }
.thinking-dots span:nth-child(3) { animation-delay: 0s; }
@keyframes dot-bounce { 0%,80%,100%{transform:scale(0);opacity:.4} 40%{transform:scale(1);opacity:1} }
.thinking-label { font-size: 12px; color: rgba(255,255,255,.5); }
.subtitle-fade-enter-active, .subtitle-fade-leave-active { transition: all .3s cubic-bezier(.4,0,.2,1); }
.subtitle-fade-enter-from, .subtitle-fade-leave-to { opacity: 0; transform: translateY(6px); }

/* 控制栏 */
.control-dock { flex-shrink: 0; padding-top: 12px; }
.dock-inner {
  background: rgba(7,10,18,.55);
  backdrop-filter: blur(18px);
  border: 1px solid rgba(255,255,255,.06);
  border-radius: 12px; padding: 12px 14px;
}
.attach-strip { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; max-height: 70px; overflow-y: auto; }
.attach-thumb { position: relative; width: 72px; height: 50px; border-radius: 6px; overflow: hidden; border: 1px solid rgba(255,255,255,.08); background: rgba(255,255,255,.03); }
.attach-thumb img { width: 100%; height: 100%; object-fit: cover; }
.attach-video-label { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; font-size: 9px; color: rgba(255,255,255,.4); padding: 3px; text-align: center; word-break: break-all; }
.attach-close { position: absolute; top: -5px; right: -5px; width: 16px; height: 16px; border-radius: 50%; border: none; background: rgba(255,255,255,.2); color: #fff; display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 9px; padding: 0; transition: background .2s; }
.attach-close:hover { background: rgba(239,68,68,.7); }
.input-row { display: flex; align-items: center; gap: 8px; }
.dock-input { flex: 1; }
.dock-input :deep(.el-textarea__inner) {
  background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.06);
  border-radius: 8px; color: rgba(255,255,255,.85);
  padding: 8px 12px; font-size: 13px; line-height: 1.5;
  min-height: 40px !important; box-shadow: none !important;
  transition: all .2s ease;
}
.dock-input :deep(.el-textarea__inner:focus) { background: rgba(255,255,255,.04); border-color: rgba(6,182,212,.35); }
.dock-input :deep(.el-textarea__inner::placeholder) { color: rgba(255,255,255,.25); }
.dock-actions { display: flex; align-items: center; gap: 5px; flex-shrink: 0; }
.dock-btn {
  width: 36px; height: 36px;
  color: rgba(255,255,255,.4) !important;
  background: rgba(255,255,255,.03) !important;
  border: 1px solid rgba(255,255,255,.06) !important;
  transition: all .2s ease !important;
}
.dock-btn:hover { color: rgba(255,255,255,.8) !important; background: rgba(255,255,255,.07) !important; border-color: rgba(255,255,255,.14) !important; }
.dock-btn.mic.recording { background: #ef4444 !important; border-color: #ef4444 !important; color: #fff !important; animation: mic-glow 1.2s infinite; }
@keyframes mic-glow { 0%,100%{box-shadow:0 0 0 0 rgba(239,68,68,.4)} 50%{box-shadow:0 0 0 6px rgba(239,68,68,0)} }
.dock-btn.send { background: linear-gradient(135deg, #ff7a1a, #d62828) !important; border: none !important; color: #fff !important; }
.dock-btn.send:hover { background: linear-gradient(135deg, #ff8f3a, #e04040) !important; transform: translateY(-1px) scale(1.04); box-shadow: 0 4px 14px rgba(214,40,40,.25); }
.dock-btn.send.is-disabled { opacity: .25 !important; transform: none !important; box-shadow: none !important; }

/* ================= 右侧 ================= */
.panel-right { min-width: 0; overflow: hidden; }
.right-inner {
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 50px;
  padding: 0 2px;
}

.media-block {
  display: flex; flex-direction: column;
  background: rgba(255,255,255,.02);
  border: 1px solid rgba(255,255,255,.06);
  border-radius: 10px;
  overflow: hidden;
}
.media-header {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid rgba(255,255,255,.05);
  background: rgba(255,255,255,.015);
  flex-shrink: 0;
}
.media-dot {
  width: 6px; height: 6px; border-radius: 50%; background: #334155;
}
.media-dot.blink { background: #ef4444; animation: blink-red 1.5s infinite; }
@keyframes blink-red { 0%,100%{opacity:1} 50%{opacity:.3} }
.media-label { font-size: 11px; color: rgba(255,255,255,.55); font-weight: 600; letter-spacing: .5px; }
.media-tag {
  margin-left: auto;
  font-size: 9px; font-weight: 700; color: #ef4444;
  padding: 1px 5px; border-radius: 3px;
  border: 1px solid rgba(239,68,68,.3);
  font-family: 'SF Mono', 'Consolas', monospace;
}
.media-counter {
  margin-left: auto;
  font-size: 10px; color: rgba(255,255,255,.3);
  font-family: 'SF Mono', 'Consolas', monospace;
}

.media-frame {
  position: relative;
  background: #000;
  overflow: hidden;
  flex-shrink: 0;
}
.media-video {
  width: 100%; height: auto; display: block;
}

/* 四个角的装饰线 */
.media-corner {
  position: absolute; width: 10px; height: 10px;
  border-color: rgba(255,122,26,.35); border-style: solid;
  pointer-events: none;
}
.media-corner.tl { top: 0; left: 0; border-width: 1px 0 0 1px; }
.media-corner.tr { top: 0; right: 0; border-width: 1px 1px 0 0; }
.media-corner.bl { bottom: 0; left: 0; border-width: 0 0 1px 1px; }
.media-corner.br { bottom: 0; right: 0; border-width: 0 1px 1px 0; }

/* 轮播 — 重叠淡入淡出，避免 mode="out-in" 黑窗 */
.carousel-frame {
  position: relative;
  width: 100%;
  min-height: 220px;
}
.carousel-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  opacity: 0;
  transform: scale(1.02);
  transition: opacity .45s ease, transform .45s ease;
  pointer-events: none;
  z-index: 0;
}
.carousel-img.active {
  opacity: 1;
  transform: scale(1);
  pointer-events: auto;
  z-index: 1;
}
.carousel-dots {
  position: absolute; bottom: 8px; left: 50%;
  transform: translateX(-50%);
  display: flex; gap: 5px; z-index: 2;
}
.dot { width: 5px; height: 5px; border-radius: 50%; border: none; background: rgba(255,255,255,.2); cursor: pointer; padding: 0; transition: all .2s ease; }
.dot.active { background: #ff7a1a; width: 14px; border-radius: 2px; }
.carousel-arrow {
  position: absolute; top: 50%; transform: translateY(-50%);
  width: 24px; height: 24px; border-radius: 4px;
  border: none; background: rgba(0,0,0,.55);
  color: rgba(255,255,255,.6);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; z-index: 2; transition: all .15s ease; font-size: 11px;
}
.carousel-arrow:hover { background: rgba(0,0,0,.8); color: #fff; }
.carousel-arrow.prev { left: 6px; }
.carousel-arrow.next { right: 6px; }

/* ================= 响应式 ================= */
@media (max-width: 1400px) {
  .showcase-body { grid-template-columns: 340px 1fr 360px; gap: 10px; padding: 10px 12px 12px; }
  .brand-title { font-size: 22px; }
  .prop-card { padding: 10px 4px; }
  .prop-ico { width: 30px; height: 30px; }
  .prop-name { font-size: 11px; }
  .prop-detail { font-size: 9px; }
}

@media (max-width: 1100px) {
  .showcase-body { grid-template-columns: 1fr; grid-template-rows: auto 1fr auto; overflow-y: auto; }
  .panel-left, .panel-right { display: none; }
}
</style>
