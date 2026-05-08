<template>
  <el-dialog
    v-model="visible"
    title="拍照"
    width="720px"
    class="camera-dialog"
    append-to-body
    @closed="stopCamera"
  >
    <div class="camera-shell">
      <video ref="videoRef" class="camera-video" autoplay playsinline muted />
      <div v-if="!streamReady" class="camera-placeholder">
        <el-icon :size="36"><Camera /></el-icon>
        <span>{{ cameraError || '正在打开摄像头...' }}</span>
      </div>
    </div>

    <template #footer>
      <div class="camera-actions">
        <el-button @click="visible = false">取消</el-button>
        <el-button :loading="starting" @click="startCamera">
          重新打开
        </el-button>
        <el-button type="primary" :disabled="!streamReady" @click="capture">
          拍照加入
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'capture', file: File): void
}>()

const visible = ref(false)
const videoRef = ref<HTMLVideoElement>()
const stream = ref<MediaStream | null>(null)
const streamReady = ref(false)
const starting = ref(false)
const cameraError = ref('')

watch(() => props.modelValue, async value => {
  visible.value = value
  if (value) {
    await nextTick()
    startCamera()
  }
})

watch(visible, value => {
  emit('update:modelValue', value)
  if (!value) stopCamera()
})

async function startCamera() {
  if (!navigator.mediaDevices?.getUserMedia) {
    cameraError.value = '当前浏览器不支持摄像头'
    return
  }
  stopCamera()
  starting.value = true
  cameraError.value = ''
  streamReady.value = false
  try {
    stream.value = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: { ideal: 'environment' },
        width: { ideal: 1280 },
        height: { ideal: 720 },
      },
      audio: false,
    })
    if (videoRef.value) {
      videoRef.value.srcObject = stream.value
      await videoRef.value.play()
      streamReady.value = true
    }
  } catch (error: any) {
    cameraError.value = error?.name === 'NotAllowedError'
      ? '摄像头权限被拒绝'
      : '摄像头打开失败'
    ElMessage.error(cameraError.value)
  } finally {
    starting.value = false
  }
}

function stopCamera() {
  stream.value?.getTracks().forEach(track => track.stop())
  stream.value = null
  streamReady.value = false
  if (videoRef.value) videoRef.value.srcObject = null
}

function capture() {
  const video = videoRef.value
  if (!video || !video.videoWidth || !video.videoHeight) return
  const canvas = document.createElement('canvas')
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
  canvas.toBlob(blob => {
    if (!blob) return
    const file = new File([blob], `camera_${Date.now()}.jpg`, { type: 'image/jpeg' })
    emit('capture', file)
    ElMessage.success('照片已加入待识别列表')
  }, 'image/jpeg', 0.9)
}
</script>

<style scoped>
.camera-shell {
  position: relative;
  min-height: 360px;
  border-radius: 8px;
  overflow: hidden;
  background: #0f172a;
}
.camera-video {
  display: block;
  width: 100%;
  max-height: 68vh;
  object-fit: contain;
  background: #0f172a;
}
.camera-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #d1d5db;
}
.camera-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
