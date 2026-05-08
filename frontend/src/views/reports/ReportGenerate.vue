<template>
  <div class="page">
    <el-card>
      <template #header><span class="section-title" style="margin:0;">生成报告</span></template>

      <el-steps :active="step" finish-status="success" align-center class="gen-steps">
        <el-step title="填写基本信息" description="标题 / 地点 / 检查人" />
        <el-step title="选择隐患记录" description="勾选需要纳入报告的图片" />
        <el-step title="生成 PDF / Word" description="自动渲染并下载" />
      </el-steps>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" style="margin-top: 18px;">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="报告标题" prop="title">
              <el-input v-model="form.title" placeholder="例:化学楼 305 - 月度消防安全检查" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="地点">
              <LabSelect v-model:lab-id="form.lab_id" v-model:other-location="form.other_location" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="检查人">
              <el-input v-model="form.inspector" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="备注">
              <el-input v-model="form.extra_notes" type="textarea" :rows="2"
                        placeholder="如关注重点、检查范围等(可选)" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">选择隐患识别记录</el-divider>

        <div class="picker-bar">
          <el-input v-model="filterLab" placeholder="地点筛选" clearable
                    style="width: 220px;" @change="loadDetections">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-button @click="loadDetections">
            <el-icon style="margin-right: 4px;"><Refresh /></el-icon>
            刷新
          </el-button>
          <span class="picker-meta" style="margin-left: auto;">
            已选 <b style="color: var(--brand-orange); font-size: 16px;">{{ form.detection_ids.length }}</b> /
            {{ detections.length }} 条
          </span>
        </div>

        <el-table ref="tableRef" :data="detections" border highlight-current-row class="picker-table"
                  @selection-change="onSelectChange" :max-height="380">
          <el-table-column type="selection" width="55" />
          <el-table-column type="index" width="50" />
          <el-table-column prop="created_at" label="时间" width="160" />
          <el-table-column prop="lab_name" label="地点" width="160" />
          <el-table-column label="预览" width="120">
            <template #default="{ row }">
              <el-image :src="row.annotated_image || row.original_image"
                        :preview-src-list="[row.annotated_image || row.original_image]"
                        style="width:80px; height:60px; border-radius:6px;"
                        fit="cover" />
            </template>
          </el-table-column>
          <el-table-column label="隐患数" width="80" align="center">
            <template #default="{ row }">
              <el-tag size="small" effect="plain">{{ row.hazard_count }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="风险" width="80">
            <template #default="{ row }">
              <el-tag :type="severityTag(row.overall_severity)">{{ severityLabel(row.overall_severity) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="summary" label="评估" show-overflow-tooltip />
        </el-table>

        <div class="action-row">
          <el-button @click="$router.back()">取消</el-button>
          <el-button type="primary" :loading="loading" @click="submit">
            <el-icon style="margin-right: 4px;"><Document /></el-icon>
            生成 PDF / Word
          </el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules, TableInstance } from 'element-plus'
import { reportApi } from '@/api/reports'
import { hazardApi } from '@/api/hazards'
import type { HazardDetection } from '@/types'
import { severityTag, severityLabel } from '@/utils/severity'
import LabSelect from '@/components/LabSelect.vue'

const router = useRouter()
const route = useRoute()
const formRef = ref<FormInstance>()
const tableRef = ref<TableInstance>()
const loading = ref(false)

const form = reactive({
  title: '',
  lab_id: null as number | null,
  other_location: '',
  inspector: '',
  detection_ids: [] as number[],
  extra_notes: '',
})

const rules: FormRules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
}

const detections = ref<HazardDetection[]>([])
const filterLab = ref('')
const initialDetectionIds = computed(() => String(route.query.detection_ids || '')
  .split(',')
  .map(id => Number(id))
  .filter(id => Number.isFinite(id) && id > 0))

const step = computed(() => {
  if (loading.value) return 2
  if (form.title && form.detection_ids.length) return 2
  if (form.title) return 1
  return 0
})

async function loadDetections() {
  const r = await hazardApi.list({ page: 1, page_size: 100, lab_name: filterLab.value || undefined })
  detections.value = r.results || []
  await nextTick()
  applyInitialSelection()
}

function applyInitialSelection() {
  if (!initialDetectionIds.value.length || !tableRef.value) return
  const idSet = new Set(initialDetectionIds.value)
  const rows = detections.value.filter(item => idSet.has(item.id))
  rows.forEach(row => tableRef.value?.toggleRowSelection(row, true))
  if (!form.detection_ids.length && rows.length) {
    onSelectChange(rows)
  }
}

function onSelectChange(rows: HazardDetection[]) {
  form.detection_ids = rows.map(r => r.id)
  if (!form.lab_id && !form.other_location && rows.length) {
    const first = rows[0]
    if (first.lab) {
      form.lab_id = first.lab
    } else {
      form.other_location = first.lab_name || ''
    }
  }
}

async function submit() {
  if (!formRef.value) return
  await formRef.value.validate()
  if (!form.detection_ids.length) {
    ElMessage.warning('请至少选择 1 条隐患识别记录')
    return
  }
  loading.value = true
  try {
    const report = await reportApi.generate(form)
    ElMessage.success('报告已生成')
    router.replace(`/reports/${report.id}`)
  } finally {
    loading.value = false
  }
}

onMounted(loadDetections)
</script>

<style scoped>
.gen-steps {
  padding: 12px 0 4px;
  border-bottom: 1px dashed var(--line-soft);
  margin-bottom: 4px;
}
.gen-steps :deep(.el-step__title.is-process),
.gen-steps :deep(.el-step__title.is-finish) {
  color: var(--txt-primary); font-weight: 600;
}
.gen-steps :deep(.el-step__head.is-process) { color: var(--brand-orange); border-color: var(--brand-orange); }
.gen-steps :deep(.el-step__head.is-finish) { color: var(--brand-orange); border-color: var(--brand-orange); }

.picker-bar {
  display: flex; gap: 10px; align-items: center;
  padding: 10px 12px;
  background: linear-gradient(180deg, #fafbfc 0%, #f3f5fa 100%);
  border: 1px solid var(--line-soft);
  border-radius: 8px;
  margin-bottom: 10px;
}
.picker-meta { color: var(--txt-secondary); font-size: 13px; }
.picker-table :deep(.el-table__row) { transition: background .2s ease; }

.action-row {
  margin-top: 18px;
  padding-top: 14px;
  border-top: 1px dashed var(--line-soft);
  display: flex; gap: 10px; justify-content: flex-end;
}
</style>
