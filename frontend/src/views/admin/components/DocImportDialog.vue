<template>
  <el-dialog
    v-model="visible"
    title="智能导入培训方案"
    width="1000px"
    :close-on-click-modal="false"
    destroy-on-close
  >
    <div class="import-container" v-loading="loading" :element-loading-text="loadingText">
      <!-- 第一步：上传 -->
      <div v-if="step === 'upload'" class="upload-step">
        <el-upload
          drag
          action=""
          :auto-upload="false"
          :show-file-list="false"
          :on-change="handleFileChange"
          accept=".pdf,.pptx"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将 PPTX 或 PDF 拖到此处，或 <em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持多模态大模型深度识别，系统将自动生成教学讲义与演练题目
            </div>
          </template>
        </el-upload>
      </div>

      <!-- 第二步：预览与修改 -->
      <div v-if="step === 'preview'" class="preview-step">
        <el-alert 
          title="AI 已完成文档深度识别。请在下方核对并微调生成的教学内容与测试题目，确认无误后点击“确认并导入库”。" 
          type="success" 
          :closable="false" 
          show-icon 
        />
        
        <div class="preview-layout">
          <div class="teaching-side">
            <div class="section-header">
              <h3>📖 培训教学讲义</h3>
              <el-tag size="small">Markdown 格式</el-tag>
            </div>
            <el-input
              type="textarea"
              v-model="previewData.teaching_content"
              :rows="22"
              placeholder="生成的教学讲义内容..."
            />
          </div>
          <div class="scenario-side">
            <div class="section-header">
              <h3>🎯 配套演练题目 ({{ previewData.scenarios?.length }})</h3>
            </div>
            <div class="scenario-list">
              <el-card v-for="(item, index) in previewData.scenarios" :key="index" class="scenario-item">
                <template #header>
                  <div class="card-header">
                    <el-input v-model="item.title" placeholder="题目名称" style="flex: 1" />
                    <el-select v-model="item.difficulty" size="small" style="width: 100px">
                      <el-option label="低难度" value="low" />
                      <el-option label="中难度" value="medium" />
                      <el-option label="高难度" value="high" />
                    </el-select>
                    <el-button type="danger" link @click="removeScenario(index)"><el-icon><Delete /></el-icon></el-button>
                  </div>
                </template>
                <div class="item-field">
                  <label>场景描述：</label>
                  <el-input type="textarea" v-model="item.description" :rows="2" />
                </div>
                <div class="item-field">
                  <label>标准处置流程：</label>
                  <el-input type="textarea" v-model="item.correct_actions" :rows="2" />
                </div>
                <div class="item-field">
                  <label>专家分析：</label>
                  <el-input type="textarea" v-model="item.analysis" :rows="2" />
                </div>
              </el-card>
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div v-if="step === 'upload'">
        <el-button @click="visible = false">取消</el-button>
      </div>
      <div v-else>
        <el-button @click="step = 'upload'">返回重新上传</el-button>
        <el-button type="primary" :loading="saving" @click="handleConfirm">确认并导入库</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { scenarioApi } from '@/api/scenarios'
import type { TrainingMaterial } from '@/api/scenarios'
import { UploadFilled, Delete } from '@element-plus/icons-vue'

const visible = ref(false)
const step = ref<'upload' | 'preview'>('upload')
const loading = ref(false)
const loadingText = ref('')
const saving = ref(false)

const material = ref<TrainingMaterial | null>(null)
const previewData = reactive({
  teaching_content: '',
  scenarios: [] as any[]
})

async function handleFileChange(file: any) {
  if (!file.raw) return
  
  loading.value = true
  loadingText.value = '正在上传文档...'
  
  try {
    const formData = new FormData()
    formData.append('file', file.raw)
    
    // 1. 上传
    const res: any = await scenarioApi.uploadMaterial(formData)
    material.value = res
    
    // 2. 开始处理
    loadingText.value = '大模型正在通过多模态识别深度解析文档，请稍候...'
    const processRes: any = await scenarioApi.processMaterial(material.value!.id)
    
    previewData.teaching_content = processRes.result_teaching
    previewData.scenarios = processRes.result_scenarios || []
    
    step.value = 'preview'
  } catch (e: any) {
    const msg = e.response?.data?.error || e.message || '处理文档失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

function removeScenario(index: number) {
  previewData.scenarios.splice(index, 1)
}

async function handleConfirm() {
  if (!material.value) return
  if (!previewData.teaching_content || previewData.scenarios.length === 0) {
    ElMessage.warning('内容不能为空')
    return
  }
  
  saving.value = true
  try {
    await scenarioApi.confirmImport(material.value.id, {
      teaching_content: previewData.teaching_content,
      scenarios: previewData.scenarios
    })
    ElMessage.success('培训方案已成功生成并导入场景库')
    visible.value = false
    emit('success')
  } catch (e: any) {
    ElMessage.error('导入失败')
  } finally {
    saving.value = false
  }
}

const emit = defineEmits(['success'])
defineExpose({ open: () => { visible.value = true; step.value = 'upload' } })
</script>

<style scoped>
.preview-layout {
  display: flex;
  gap: 24px;
  margin-top: 20px;
  height: 65vh;
}
.teaching-side {
  flex: 4;
  display: flex;
  flex-direction: column;
}
.scenario-side {
  flex: 6;
  display: flex;
  flex-direction: column;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.section-header h3 { margin: 0; font-size: 16px; color: #1f2937; }
.scenario-list {
  overflow-y: auto;
  flex: 1;
  padding-right: 8px;
}
.scenario-item {
  margin-bottom: 16px;
  border-radius: 8px;
}
.card-header {
  display: flex;
  gap: 12px;
  align-items: center;
}
.item-field {
  margin-top: 12px;
}
.item-field label {
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  display: block;
  margin-bottom: 4px;
}
</style>
