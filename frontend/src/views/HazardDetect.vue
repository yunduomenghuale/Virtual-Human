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
            <el-form-item label="图片(jpg / png)">
              <el-upload drag :auto-upload="false" :on-change="onPick" :show-file-list="false"
                         accept="image/png,image/jpeg" style="width:100%;">
                <el-icon class="el-icon--upload" :size="48"><UploadFilled /></el-icon>
                <div class="el-upload__text">将图片拖到此处,或<em>点击选择</em></div>
                <template #tip>
                  <div class="muted">支持 JPG / PNG。建议不超过 5MB。</div>
                </template>
              </el-upload>
            </el-form-item>
            <div class="form-actions">
              <el-button type="primary" :disabled="!file" :loading="loading" @click="submit">
                开始识别
              </el-button>
              <el-button v-if="file" plain @click="reset">重置</el-button>
            </div>
          </el-form>

          <div v-if="previewUrl" style="margin-top: 14px;">
            <p class="muted" style="margin: 6px 0;">预览(原图):</p>
            <img :src="previewUrl" class="preview-img" />
          </div>
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card>
          <template #header>
            <div style="display:flex; align-items:center; justify-content:space-between;">
              <span class="section-title" style="margin:0;">识别结果</span>
              <el-tag v-if="result" :type="severityTag(result.overall_severity)" effect="dark">
                总体风险:{{ severityLabel(result.overall_severity) }}
              </el-tag>
            </div>
          </template>

          <div v-if="!result" class="placeholder">
            <div class="ph-icon">
              <el-icon :size="40" color="#ff7a1a"><Picture /></el-icon>
            </div>
            <p class="muted" style="margin: 0;">上传图片后,识别结果将展示在这里</p>
          </div>

          <div v-else>
            <div class="annotated-wrap">
              <img :src="result.annotated_image || result.original_image" />
            </div>

            <p style="margin: 10px 0; line-height: 1.7;">
              <b>整体评估:</b>{{ result.summary || '-' }}
            </p>

            <el-divider content-position="left">隐患明细 ({{ result.hazards.length }})</el-divider>

            <el-empty v-if="!result.hazards.length" description="未识别到明显隐患" />
            <el-collapse v-else>
              <el-collapse-item v-for="(h, idx) in result.hazards" :key="idx" :name="idx">
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
                <p class="muted">bbox(%): {{ h.bbox.join(', ') }}</p>
              </el-collapse-item>
            </el-collapse>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { hazardApi } from '@/api/hazards'
import type { HazardDetection } from '@/types'
import { severityTag, severityLabel } from '@/utils/severity'
import LabSelect from '@/components/LabSelect.vue'

const file = ref<File | null>(null)
const previewUrl = ref('')
const labId = ref<number | null>(null)
const otherLocation = ref('')
const extra = ref('')
const loading = ref(false)
const result = ref<HazardDetection | null>(null)

function onPick(f: any) {
  const real = f.raw || f
  if (!real) return
  file.value = real
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = URL.createObjectURL(real)
}

async function submit() {
  if (!file.value) return
  loading.value = true
  try {
    result.value = await hazardApi.detect(file.value, labId.value, otherLocation.value, extra.value)
    ElMessage.success(`识别完成,共 ${result.value!.hazards.length} 项隐患`)
  } finally {
    loading.value = false
  }
}

function reset() {
  file.value = null
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = ''
  result.value = null
}
</script>

<style scoped>
.preview-img, .annotated-wrap img {
  max-width: 100%;
  border-radius: 10px;
  box-shadow: 0 6px 20px rgba(15, 23, 42, .08);
  border: 1px solid var(--line-soft);
}
.annotated-wrap {
  position: relative;
  border-radius: 10px;
  overflow: hidden;
  background: #000;
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
