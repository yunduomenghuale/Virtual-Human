<template>
  <div class="page detect-page">
    <el-row :gutter="16">
      <el-col :span="10">
        <el-card>
          <template #header><span class="section-title" style="margin:0;">上传图片识别</span></template>

          <el-form label-position="top">
            <el-form-item label="地点">
              <LabSelect v-model:lab-id="labId" v-model:other-location="otherLocation" />
            </el-form-item>
            <el-form-item label="补充说明(可选)">
              <el-input v-model="extra" type="textarea" :rows="2"
                        placeholder="如关注重点、检查范围等" />
            </el-form-item>
            <el-form-item label="图片 / 视频">
              <el-upload drag multiple :auto-upload="false" :on-change="onPick" :on-remove="onRemove"
                         :file-list="uploadFiles" accept="image/png,image/jpeg,video/mp4,video/webm,video/quicktime" style="width:100%;">
                <el-icon class="el-icon--upload" :size="48"><UploadFilled /></el-icon>
                <div class="el-upload__text">将图片或视频拖到此处,或<em>点击选择</em></div>
                <template #tip>
                  <div class="muted">支持 JPG / PNG / MP4 / WebM / MOV。视频会自动抽帧后作为同一地点的一组识别记录。</div>
                </template>
              </el-upload>
            </el-form-item>
            <div class="form-actions">
              <el-button type="primary" :disabled="!files.length" :loading="loading" @click="submit">
                开始识别 {{ files.length ? `(${files.length} 张)` : '' }}
              </el-button>
              <el-button plain @click="cameraVisible = true">
                <el-icon style="margin-right: 4px;"><Camera /></el-icon>
                拍照
              </el-button>
              <el-button v-if="files.length" plain @click="reset">重置</el-button>
            </div>
          </el-form>

          <div v-if="previews.length" style="margin-top: 14px;">
            <p class="muted" style="margin: 6px 0;">预览(原图):</p>
            <div class="preview-grid">
              <img v-for="item in previews.filter(p => p.mediaType === 'image' || p.url)" :key="item.name" :src="item.url" class="preview-img" />
              <div v-for="item in previews.filter(p => p.mediaType === 'video' && !p.url)" :key="item.name" class="preview-video">
                <el-icon><VideoCamera /></el-icon>
                <span>{{ item.fileName }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card>
          <template #header>
            <div style="display:flex; align-items:center; justify-content:space-between;">
              <span class="section-title" style="margin:0;">识别结果</span>
              <el-tag v-if="results.length" :type="severityTag(overallSeverity)" effect="dark">
                总体风险:{{ severityLabel(overallSeverity) }}
              </el-tag>
            </div>
          </template>

          <div v-if="!results.length" class="placeholder">
            <div class="ph-icon">
              <el-icon :size="40" color="#ff7a1a"><Picture /></el-icon>
            </div>
            <p class="muted" style="margin: 0;">上传一组图片后,识别结果将按图片展示在这里</p>
          </div>

          <div v-else>
            <div class="batch-summary">
              <span>共识别 {{ results.length }} 张图片,发现 {{ totalHazards }} 项隐患。</span>
              <el-button type="primary" size="small" @click="createReportFromResults">
                生成这组图片的报告
              </el-button>
            </div>

            <el-tabs v-model="activeResultId" type="border-card">
              <el-tab-pane v-for="(item, index) in results" :key="item.id"
                           :label="`图片 ${index + 1} (${item.hazard_count})`"
                           :name="String(item.id)">
                <div class="annotated-wrap">
                  <img :src="item.annotated_image || item.original_image" />
                </div>

                <p style="margin: 10px 0; line-height: 1.7;">
                  <b>整体评估:</b>{{ item.summary || '-' }}
                </p>

                <el-divider content-position="left">隐患明细 ({{ item.hazards.length }})</el-divider>

                <el-empty v-if="!item.hazards.length" description="未识别到明显隐患" />
                <el-collapse v-else>
                  <el-collapse-item v-for="(h, idx) in item.hazards" :key="idx" :name="idx">
                    <template #title>
                      <span class="hz-num">{{ idx + 1 }}</span>
                      <span style="font-weight:600;">{{ h.name }}</span>
                      <el-tag size="small" effect="plain" style="margin-left: 8px;">{{ h.category }}</el-tag>
                      <el-tag size="small" :type="severityTag(h.severity)" style="margin-left: 6px;">
                        {{ severityLabel(h.severity) }}
                      </el-tag>
                    </template>
                    <p><b>描述:</b>{{ h.description }}</p>
                    <p><b>建议:</b>{{ h.suggestion }}</p>
                    <p v-if="h.bbox" class="muted">bbox(%): {{ h.bbox.join(', ') }}</p>
                  </el-collapse-item>
                </el-collapse>
              </el-tab-pane>
            </el-tabs>
          </div>
        </el-card>
      </el-col>
    </el-row>
    <CameraCapture v-model="cameraVisible" @capture="addCameraImage" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElNotification } from 'element-plus'
import type { UploadFile, UploadFiles, UploadUserFile } from 'element-plus'
import { hazardApi } from '@/api/hazards'
import type { HazardDetection, Severity } from '@/types'
import { severityTag, severityLabel } from '@/utils/severity'
import LabSelect from '@/components/LabSelect.vue'
import CameraCapture from '@/components/CameraCapture.vue'
import { extractVideoCover } from '@/utils/videoCover'

const router = useRouter()
const files = ref<{ file: File; mediaType: 'image' | 'video' }[]>([])
const uploadFiles = ref<UploadUserFile[]>([])
const previews = ref<{ name: string; url: string; mediaType: 'image' | 'video'; fileName: string }[]>([])
const cameraVisible = ref(false)
const labId = ref<number | null>(null)
const otherLocation = ref('')
const extra = ref('')
const loading = ref(false)
const results = ref<HazardDetection[]>([])
const activeResultId = ref('')

const totalHazards = computed(() => results.value.reduce((sum, item) => sum + item.hazard_count, 0))
const overallSeverity = computed<Severity>(() => {
  if (results.value.some(item => item.overall_severity === 'high')) return 'high'
  if (results.value.some(item => item.overall_severity === 'medium')) return 'medium'
  return 'low'
})

async function syncFiles(list: UploadFiles) {
  previews.value.forEach(item => URL.revokeObjectURL(item.url))
  files.value = list.reduce<{ file: File; mediaType: 'image' | 'video' }[]>((acc, item) => {
    if (item.raw && (item.raw.type.startsWith('image/') || item.raw.type.startsWith('video/'))) {
      acc.push({ file: item.raw, mediaType: item.raw.type.startsWith('video/') ? 'video' : 'image' })
    }
    return acc
  }, [])
  previews.value = []
  for (const item of files.value) {
    let url = ''
    if (item.mediaType === 'image') {
      url = URL.createObjectURL(item.file)
    } else {
      try {
        url = await extractVideoCover(item.file)
      } catch {
        url = ''
      }
    }
    previews.value.push({
      name: `${item.file.name}-${item.file.lastModified}`,
      url,
      mediaType: item.mediaType,
      fileName: item.file.name,
    })
  }
}

async function onPick(_file: UploadFile, list: UploadFiles) {
  await syncFiles(list)
}

async function onRemove(_file: UploadFile, list: UploadFiles) {
  await syncFiles(list)
}

function addCameraImage(file: File) {
  files.value.push({ file, mediaType: 'image' })
  previews.value.push({
    name: `${file.name}-${file.lastModified}`,
    url: URL.createObjectURL(file),
    mediaType: 'image',
    fileName: file.name,
  })
}

import { playFireTruckAlert } from '@/utils/alertSound'

function notifyHighRisk(detection: HazardDetection) {
  playFireTruckAlert()
  ElNotification({
    title: '高风险预警',
    message: `${detection.lab_name || '未填写'} 发现 ${detection.hazard_count} 项高风险隐患`,
    type: 'error',
    duration: 0,
    position: 'top-right',
    dangerouslyUseHTMLString: true,
    customClass: 'high-risk-alert',
  })
}

async function submit() {
  if (!files.value.length) return
  loading.value = true
  try {
    const resp = await hazardApi.detectMedia(files.value, labId.value, otherLocation.value, extra.value)
    results.value = Array.isArray((resp as any).results) ? (resp as any).results : [resp as HazardDetection]
    activeResultId.value = results.value[0] ? String(results.value[0].id) : ''
    ElMessage.success(`识别完成,${results.value.length} 张图片共 ${totalHazards.value} 项隐患`)
    // 高风险弹窗提醒
    results.value.forEach((det) => {
      if (det.overall_severity === 'high') notifyHighRisk(det)
    })
  } finally {
    loading.value = false
  }
}

function reset() {
  files.value = []
  uploadFiles.value = []
  previews.value.forEach(item => URL.revokeObjectURL(item.url))
  previews.value = []
  results.value = []
  activeResultId.value = ''
}

function createReportFromResults() {
  if (!results.value.length) return
  const ids = results.value.map(item => item.id).join(',')
  router.push({ path: '/reports/new', query: { detection_ids: ids } })
}
</script>

<style scoped>
.preview-img, .annotated-wrap img {
  max-width: 100%;
  border-radius: 10px;
  box-shadow: 0 6px 20px rgba(15, 23, 42, .08);
  border: 1px solid var(--line-soft);
}
.preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(96px, 1fr));
  gap: 10px;
}
.preview-grid .preview-img {
  width: 100%;
  aspect-ratio: 4 / 3;
  object-fit: cover;
}
.preview-video {
  aspect-ratio: 4 / 3;
  border: 1px solid var(--line-soft);
  border-radius: 10px;
  background: #f8fafc;
  color: var(--txt-secondary);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px;
  text-align: center;
  word-break: break-all;
  font-size: 12px;
}
.annotated-wrap {
  position: relative;
  border-radius: 10px;
  overflow: hidden;
  background: #000;
}
.batch-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  margin-bottom: 12px;
  border: 1px solid var(--line-soft);
  border-radius: 8px;
  background: #fafbfc;
  color: var(--txt-secondary);
}
.placeholder {
  text-align: center;
  padding: 80px 0;
  display: flex; flex-direction: column; align-items: center; gap: 12px;
}
.placeholder .ph-icon {
  width: 84px; height: 84px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, rgba(255,122,26,.12), rgba(214,40,40,.10));
}
.hz-num {
  display: inline-flex; width: 22px; height: 22px; border-radius: 50%;
  background: linear-gradient(135deg, #ff7a1a 0%, #d62828 100%);
  color: #fff; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700;
  margin-right: 8px;
  box-shadow: 0 2px 6px rgba(214,40,40,.3);
}
:deep(.el-collapse-item__header) {
  padding-left: 6px;
  font-size: 14px;
}
:deep(.el-upload-dragger) {
  border-radius: 10px !important;
  border: 1.5px dashed var(--line) !important;
  background: #fafbfc !important;
  transition: border-color .2s ease, background .2s ease;
}
:deep(.el-upload-dragger:hover) {
  border-color: var(--brand-orange) !important;
  background: #fff8ee !important;
}
.el-upload__text em { color: var(--brand-orange); font-style: normal; font-weight: 600; }
.form-actions {
  display: flex; gap: 10px;
  margin-top: 4px;
  padding-top: 14px;
  border-top: 1px dashed var(--line-soft);
}
</style>
